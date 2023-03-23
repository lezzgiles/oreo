#!/usr/bin/env python3

from functools import lru_cache
from copy import deepcopy

import sys
import re

class ParseFailException(Exception): pass
class ParseDefinitionException(Exception): pass

class LocationTracker:
    def __init__(self,text,offset=0,newline=True,indents=None):
        self._text = text
        self._offset = offset
        self._newline = newline
        self._last_indent = 0
        self._highwatermark = 0

    def text(self):
        return self._text[self._offset:]

    def last_indent(self): return self._last_indent

    def match(self,regex,flags=0):
        """
        If regex matches text, return the match and
        move up the location; otherwise raise exception.
        """
        m = re.match(regex,self.text(),flags)
        if m:
            self._offset += len(m.group())
            m2 = re.search('\n$',m.group())
            if m2:
                self._newline = True
            else:
                self._newline = False
            return m.group()
        else:
            raise ParseFailException

    def match_bool(self,regex,flags=0):
        """
        If regex matches text, return True and move up
        the location; otherwise return False
        """
        try:
            self.match(regex,flags)
        except ParseFailException:
            return False
        return True

    def strip_trailing_whitespace(self):
        self.match_bool('[ \t]*\n')

    def strip_other_whitespace(self):
        try:
            previous_newline = self._newline
            spaces = self.match('[ \t]*')
            if previous_newline:
                self._last_indent = len(spaces)
            if len(spaces) > 0:
                return True
            else:
                return False
        except:
            return False
                
    def backtrack(self,location):
        self._text = location._text
        self._offset = location._offset
        self._newline = location._newline

    def copy(self):
        return LocationTracker(self._text,self._offset,self._newline)

class Tokenizer:
    def __init__(self,ignore_whitespace=True):
        self.tokens = {}
        self.ignore_whitespace = ignore_whitespace
        self.comment_styles = []
        self.indent_tokens = ()
        self.indents = [0]

    def add_token(self,name,regex,walk=None):
        self.tokens[name] = {'regex':regex,'walk':walk}

    def add_comment_style(self,regex,flags=0):
        self.comment_styles.append((regex,flags))

    def use_indent_tokens(self,indent_token,outdent_token,tabsize=0):
        if not self.ignore_whitespace:
            raise ParseDefinitionException("Cannot use indent/outdent tokens and not ignore_whitespace")
        self.indent_tokens = (indent_token,outdent_token)
        self.tabsize = tabsize
        
    def next_token(self,name,location):
        self.strip_whitespace_and_comments(location)
        location._highwatermark = location._offset
        
        # Now we've stripped everything, comments and spaces, up to
        # the next real thing, so look at the indent level.  We look
        # at the level before every token, but it won't change in the same line
        if self.indent_tokens:
            current_indent = location.last_indent()
            
            if current_indent > self.indents[-1]:
                # Indent increased
                self.indents.append(current_indent)
                if name == self.indent_tokens[0]:
                    return Token(self.indent_tokens[0],current_indent)
                else:
                    raise ParseFailException("Mismatch: expecting {name} but got {self.indent_tokens[0]}")
                    
            elif not current_indent in self.indents:
                raise ParseFailException("Outdent to non-matching indentation level")
            
            elif current_indent < self.indents[-1]:
                # Indent decreased
                self.indents.pop()
                if name == self.indent_tokens[1]:
                    return Token(self.indent_tokens[1],current_indent)
                else:
                    raise ParseFailException("Mismatch: expecting {name} but got {self.indent_tokens[1]}")

        # If we are expecting the INDENT or OUTDENT tokens but didn't see one, that's an error
        if name in self.indent_tokens:
            raise ParseFailException
        
        value = location.match(self.tokens[name]['regex'])
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
                if location.strip_other_whitespace(): modified = True
                
            for (comment_style,flags) in self.comment_styles:
                if location.match_bool(comment_style, flags):
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

    def add_rule(self,name,body,tokenizer=None):
        self.rules[name] = {'body':body,'tokenizer':tokenizer}
    
    def parse(self,text):
        if 'start' not in self.rules:
            raise ParseDefinitionException("There must be a special top rule named \'start\'")
        if not self.rules['start']['tokenizer']:
            raise ParseDefinitionException("\'start\' rule must specify a tokenizer")
        location = LocationTracker(text)
        try:
            tree = self.parse_rule('start',location,tokenizer=self.rules['start']['tokenizer'])
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

    def parse_element(self,element,location,tokenizer):
        """
        Parse element, which can be a terminal or a non-terminal.
        Return a Node or a Token and an updated location, or raise ParseFailException
        """
        if element in list(tokenizer.tokens)+list(tokenizer.indent_tokens):
            tree = tokenizer.next_token(element,location)
        elif element in self.rules:
            tree = self.parse_rule(element,location,tokenizer)
        else:
            raise ParseDefinitionException(f"element {element} not defined")
        return tree

    def parse_grammar_item(self,element,location,tokenizer):
        elt,matches_specifiers = Parser.expand_grammar_item(element)
        if not matches_specifiers:
            return self.parse_element(elt,location,tokenizer)
        else:
            retval = []
            count = 0
            while True:
                try:
                    tree = self.parse_element(elt,location,tokenizer)
                    retval.append(tree)
                except ParseFailException:
                    if matches_specifiers[0] > count:
                        raise ParseFailException(f"Not enough terms match in list")
                    break
                count += 1
                if matches_specifiers[1] and count == matches_specifiers[1]: break
            return retval
                    
    
    def parse_rule(self,rule,location,tokenizer=None):

        if rule not in self.rules:
            raise ParseDefinitionException("Parse error: Rule {rule} not in rules")

        for pattern,walk_function in self.rules[rule]['body']:
            node = Node(rule,walk_function)
            saved_location = deepcopy(location)
            try:
                for element in pattern:
                    tree = self.parse_grammar_item(element,location,tokenizer)
                    node.add_child(tree)
                # Got a complete match, so we are done!
                break
            except ParseFailException:
                location.backtrack(saved_location)

        else:
            raise ParseFailException(f"Could not match pattern {pattern}")
            
        return node
        
