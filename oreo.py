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

    def add_token(self,name,regex,value=None):
        self.tokens[name] = {'regex':regex,'value':value}

    def next_token(self,name,text,offset):
        offset = self.strip_whitespace(text,offset)
        m = re.match(self.tokens[name]['regex'],text[offset:])
        if m:
            offset += len(m.group())
            return Token(name,m.group(),self.tokens[name]['value']),offset
        else:
            raise ParseFailException("Cannot match token")
        
    def strip_whitespace(self,text,offset):
        if self.ignore_whitespace:
            m = re.match('\s+',text[offset:])
            if m:
                offset += len(m.group())
        return offset

class Token:
    def __init__(self,token,body,value):
        self.token = token
        self.body = body
        self.value_function = value

    def value(self):
        if self.value_function:
            return self.value_function(self.body)
        else:
            return self.body
        
class Node:
    def __init__(self,rule,value):
        self.rule = rule
        self.children = []
        self.value_function = value

    def add_child(self,child):
        self.children.append(child)

    def value(self):
        return self.value_function(*self.children)

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
        offset = self.rules['start']['tokenizer'].strip_whitespace(text,offset)
        if offset != len(text):
            raise ParseFailException(f"Extra input found after input: {text[offset:]}")
        return tree

    def parse_element(element):
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

    def parse_thing(self,element,text,offset,tokenizer):
        """
        Parse element, which can be a terminal or a non-terminal.
        Return a Node or a Token and an updated offset, or raise ParseFailException
        """
        if element in tokenizer.tokens:
            thing,offset = tokenizer.next_token(element,text,offset)
        elif element in self.rules:
            thing,offset = self.parse_rule(element,text,offset,tokenizer)
        else:
            raise ParseDefinitionException(f"element {element} not defined")
        return thing,offset

    def parse_syntax_thing(self,element,text,offset,tokenizer):
        elt,matches = Parser.parse_element(element)
        if not matches:
            return self.parse_thing(elt,text,offset,tokenizer)
        else:
            retval = []
            count = 0
            while True:
                try:
                    node,offset = self.parse_thing(elt,text,offset,tokenizer)
                    retval.append(node)
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

        for pattern,value_function in self.rules[rule]['body']:
            node = Node(rule,value_function)
            saved_offset = offset
            try:
                for element in pattern:
                    thing,offset = self.parse_syntax_thing(element,text,offset,tokenizer)
                    node.add_child(thing)
                # Got a complete match, so we are done!
                break
            except ParseFailException:
                offset = saved_offset

        else:
            raise ParseFailException(f"Could not match pattern {pattern}")
            
        return node,offset
        
