#!/usr/bin/env python3

from functools import lru_cache
import sys
import re

class ParseFailException(Exception): pass
class ParseDefinitionException(Exception): pass

class Tokenizer:
    def __init__(self,ignore_whitespace=True):
        self.tokens = {}
        self.ignore_whitespace = ignore_whitespace
        self.comment_styles = []
        self.indent_tokens = ()

    def eat(cls,text,offset,regex,flags=0):
        m = re.match(regex,text[offset:],flags)
        if m:
            offset += len(m.group())

    def add_token(self,name,regex,walk=None):
        self.tokens[name] = {'regex':regex,'walk':walk}

    def add_comment_style(self,regex,flags=0):
        self.comment_styles.append((regex,flags))

    def use_indent_tokens(self,indent_token,outdent_token,tabsize=0):
        if not self.ignore_whitespace:
            raise ParseDefinitionException("Cannot use indent/outdent tokens and not ignore_whitespace")
        self.indent_tokens = (indent_token,outdent_token)
        self.tabsize = tabsize
        
    def next_token(self,name,text,offset):
        offset = self.strip_whitespace_and_comments(text,offset)
        m = re.match(self.tokens[name]['regex'],text[offset:],)
        if m:
            offset += len(m.group())
            return Token(name,m.group(),self.tokens[name]['walk']),offset
        else:
            raise ParseFailException("Cannot match token")
        
    def strip_whitespace_and_comments(self,text,offset):
        # Repeatedly try removing whitespace and comments
        modified = True
        while modified:
            modified = False
            if self.ignore_whitespace:
                # End of line?
                m = re.match('\s+',text[offset:])
                if m:
                    offset += len(m.group())
                    modified = True
            for (comment_style,flags) in self.comment_styles:
                m = re.match(comment_style,text[offset:],flags)
                if m:
                    offset += len(m.group())
                    modified = True
        return offset

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
        tree,offset = self.parse_rule('start',text,0,tokenizer=self.rules['start']['tokenizer'])
        offset = self.rules['start']['tokenizer'].strip_whitespace_and_comments(text,offset)
        if offset != len(text):
            raise ParseFailException(f"Extra input found after input: {text[offset:]}")
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

    def parse_element(self,element,text,offset,tokenizer):
        """
        Parse element, which can be a terminal or a non-terminal.
        Return a Node or a Token and an updated offset, or raise ParseFailException
        """
        if element in list(tokenizer.tokens)+list(tokenizer.indent_tokens):
            tree,offset = tokenizer.next_token(element,text,offset)
        elif element in self.rules:
            tree,offset = self.parse_rule(element,text,offset,tokenizer)
        else:
            raise ParseDefinitionException(f"element {element} not defined")
        return tree,offset

    def parse_grammar_item(self,element,text,offset,tokenizer):
        elt,matches = Parser.expand_grammar_item(element)
        if not matches:
            return self.parse_element(elt,text,offset,tokenizer)
        else:
            retval = []
            count = 0
            while True:
                try:
                    tree,offset = self.parse_element(elt,text,offset,tokenizer)
                    retval.append(tree)
                except ParseFailException:
                    if matches[0] > count:
                        raise ParseFailException(f"Not enough terms match in list")
                    break
                count += 1
                if matches[1] and count == matches[1]: break
            return retval,offset
                    
    
    @lru_cache
    def parse_rule(self,rule,text,offset,tokenizer=None):
        if rule not in self.rules:
            raise ParseDefinitionException("Parse error: Rule {rule} not in rules")

        for pattern,walk_function in self.rules[rule]['body']:
            node = Node(rule,walk_function)
            saved_offset = offset
            try:
                for element in pattern:
                    tree,offset = self.parse_grammar_item(element,text,offset,tokenizer)
                    node.add_child(tree)
                # Got a complete match, so we are done!
                break
            except ParseFailException:
                offset = saved_offset

        else:
            raise ParseFailException(f"Could not match pattern {pattern}")
            
        return node,offset
        
