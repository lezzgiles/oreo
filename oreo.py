#!/usr/bin/env python3

from functools import lru_cache
from copy import deepcopy,copy

import sys
import re

class ParseFailException(Exception): pass
class ParseDefinitionException(Exception): pass

class LocationTracker:
    def __init__(self,text,offset=0,column=0,indents=None):
        self._text = text
        self._offset = offset
        self._column = column
        self._last_indent = 0
        if indents:
            self._indents = indents
        else:
            self._indents = [0]
        self._highwatermark = 0

    def text(self):
        return self._text[self._offset:]

    def last_indent(self): return self._last_indent

    def match(self,regex,tabsize=0,flags=0):
        """
        If regex matches text, return the match and
        move up the location; otherwise raise exception.
        """
        m = re.match(regex,self.text(),flags)
        if m:
            self._offset += len(m.group())
            m2 = re.search('\n$',m.group())
            if m2:
                self._column = 0
            else:
                self._column += len(m.group())+(m.group().count("\t")*(tabsize-1))
            return m.group()
        else:
            raise ParseFailException

    def match_bool(self,regex,tabsize=0,flags=0):
        """
        If regex matches text, return True and move up
        the location; otherwise return False
        """
        try:
            self.match(regex,tabsize,flags)
        except ParseFailException:
            return False
        return True

    def strip_trailing_whitespace(self,tabsize=0):
        self.match_bool('[ \t]*\n',tabsize)

    def strip_other_whitespace(self,tabsize):
        try:
            starting_column = self._column
            spaces = self.match('[ \t]*',tabsize)
            if starting_column == 0:
                self._last_indent = self._column
            if len(spaces) > 0:
                return True
            else:
                return False
        except:
            return False
                
    def backtrack(self,location):
        self._text = location._text
        self._offset = location._offset
        self._column = location._column
        self._last_indent = location._last_indent
        self._indents = copy(location._indents)
        self.highwatermark = location._highwatermark

class Tokenizer:
    def __init__(self,ignore_whitespace=True):
        self.tokens = {}
        self.ignore_whitespace = ignore_whitespace
        self.comment_styles = []
        self.indent_tokens = ()
        self.tabsize = 0
        self.inline_indents = False

    def add_token(self,name,regex,walk=None):
        self.tokens[name] = {'regex':regex,'walk':walk}

    def add_comment_style(self,regex,flags=0):
        self.comment_styles.append((regex,flags))

    def use_indent_tokens(self,indent_token,outdent_token,tabsize=0,inline_indents=False):
        if not self.ignore_whitespace:
            raise ParseDefinitionException("Cannot use indent/outdent tokens and not ignore_whitespace")
        self.indent_tokens = (indent_token,outdent_token)
        self.tabsize = tabsize
        self.inline_indents = inline_indents
        
    def next_token(self,name,location):
        self.strip_whitespace_and_comments(location)
        location._highwatermark = location._offset
        
        # Now we've stripped everything, comments and spaces, up to
        # the next real thing, so look at the indent level.  We look
        # at the level before every token, but it won't change in the same line
        if self.indent_tokens:
            current_indent = location.last_indent()
            
            if current_indent > location._indents[-1]:
                # Indent increased
                location._indents.append(current_indent)
                if name == self.indent_tokens[0]:
                    return Token(self.indent_tokens[0],current_indent)
                else:
                    raise ParseFailException("Mismatch: expecting {name} but got {self.indent_tokens[0]}")
                    
            elif not current_indent in location._indents:
                raise ParseFailException("Outdent to non-matching indentation level")
            
            elif current_indent < location._indents[-1]:
                # Indent decreased
                location._indents.pop()
                if name == self.indent_tokens[1]:
                    return Token(self.indent_tokens[1],current_indent)
                else:
                    raise ParseFailException("Mismatch: expecting {name} but got {self.indent_tokens[1]}")

        # If we are expecting an INDENT then it could be a same-line indent
        if self.indent_tokens and name == self.indent_tokens[0] and self.inline_indents:
            current_indent = location._column
            location._indents.append(current_indent)
            location._last_indent = current_indent
            return Token(self.indent_tokens[0],current_indent)
            
        # If we are expecting the INDENT or OUTDENT tokens but didn't see one, that's an error
        if name in self.indent_tokens:
            raise ParseFailException
        
        value = location.match(self.tokens[name]['regex'],self.tabsize)
        location._highwatermark = location._offset
        return Token(name,value,self.tokens[name]['walk'])
        
    def strip_whitespace_and_comments(self,location):
        # Repeatedly try removing whitespace and comments
        modified = True
        while modified:
            modified = False
            if self.ignore_whitespace:
                # Trailing whitespace
                if location.strip_trailing_whitespace(): modified = True
                # Non-trailing whitespace
                if location.strip_other_whitespace(self.tabsize): modified = True
                
            for (comment_style,flags) in self.comment_styles:
                if location.match_bool(comment_style, self.tabsize, flags):
                    modified = True

class Token:
    def __init__(self,token,body,walk_function=None):
        self.token = token
        self.body = body
        self.walk_function = walk_function

    def walk(self,*context):
        if self.walk_function:
            return self.walk_function(*context,self.body)
        else:
            return self.body
        
class Node:
    def __init__(self,rule,walk_function):
        self.rule = rule
        self.children = []
        self.walk_function = walk_function

    def add_child(self,child):
        self.children.append(child)

    def walk(self,*context):
        return self.walk_function(*context,*self.children)

class Parser:
    def __init__(self):
        self.rules = {}

    def trace(self,indent,message):
        if self._trace: print(f"{indent}{message}",file=sys.stderr)
        
    def add_rule(self,name,body,tokenizer=None):
        self.rules[name] = {'body':body,'tokenizer':tokenizer}
    
    def parse(self,text,trace=False):
        
        self._trace = trace
        
        if 'start' not in self.rules:
            raise ParseDefinitionException("There must be a special top rule named \'start\'")
        if not self.rules['start']['tokenizer']:
            raise ParseDefinitionException("\'start\' rule must specify a tokenizer")
        location = LocationTracker(text)
        try:
            tree = self.parse_rule('start',location,tokenizer=self.rules['start']['tokenizer'],indent="")
        except ParseFailException:
            raise ParseFailException(f"Failed to parse: Failed around: {location._text[location._highwatermark:]}")
        
        self.rules['start']['tokenizer'].strip_whitespace_and_comments(location)
        if location.text() != "":
            raise ParseFailException(f"Extra input found after input: {location.text()}")
        return tree

    def expand_grammar_item(element):
        """
        Looks at an element in the grammar, e.g. this+, and returns the element name
        'this' and the minimum and maximum number of instances, for example:
        'this+' => 'this',(1,None)
        'this*' => 'this',(0,None)
        'this?' => 'this',(0,1)
        'this' => 'this',()
        """
        m = re.match('([a-zA-Z0-9_-]+)(.*)',element)
        if not m:
            raise ParseDefinitionException(f"Parse Error: token {element} misformed")
        if m.group(2) == '+': matches = ( 1,None )
        elif m.group(2) == '*': matches = ( 0,None )
        elif m.group(2) == '?': matches = ( 0,1 )
        elif m.group(2) == '': matches = ()
        
        return m.group(1),matches

    def parse_element(self,element,location,tokenizer,indent):
        """
        Parse element, which can be a terminal or a non-terminal.
        Return a Node or a Token and an updated location, or raise ParseFailException
        """
        if element in list(tokenizer.tokens)+list(tokenizer.indent_tokens):
            tree = tokenizer.next_token(element,location)
        elif element in self.rules:
            tree = self.parse_rule(element,location,tokenizer,indent)
        else:
            raise ParseDefinitionException(f"element {element} not defined")
        return tree

    def parse_grammar_item(self,element,location,tokenizer,indent):
        elt,matches_specifiers = Parser.expand_grammar_item(element)
        if not matches_specifiers:
            return self.parse_element(elt,location,tokenizer,indent=indent+"  ")
        else:
            retval = []
            count = 0
            while True:
                try:
                    tree = self.parse_element(elt,location,tokenizer,indent=indent+"  ")
                    retval.append(tree)
                except ParseFailException:
                    if matches_specifiers[0] > count:
                        raise ParseFailException(f"Not enough terms match in list")
                    break
                count += 1
                if matches_specifiers[1] and count == matches_specifiers[1]: break
            return retval
                    
    
    def parse_rule(self,rule,location,tokenizer=None,indent=""):

        if rule not in self.rules:
            raise ParseDefinitionException("Parse error: Rule {rule} not in rules")

        self.trace(indent,f"Trying to expand {rule} with text {location.text()}")
        for pattern,walk_function in self.rules[rule]['body']:
            self.trace(indent,f" Looking at {pattern}")
            node = Node(rule,walk_function)
            saved_location = deepcopy(location)
            try:
                for element in pattern:
                    tree = self.parse_grammar_item(element,location,tokenizer,indent=indent+"  ")
                    self.trace(indent,f"  Got match for {element}")
                    node.add_child(tree)
                # Got a complete match, so we are done!
                self.trace(indent,f" Got a complete match for {pattern}")
                break
            except ParseFailException:
                self.trace(indent,f" Failed a complete match for {pattern}")
                location.backtrack(saved_location)

        else:
            raise ParseFailException(f"Could not match pattern {pattern}")
            
        return node
        
