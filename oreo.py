#!/usr/bin/env python3

import sys
import re

class ParseFailException(Exception): pass
class ParseDefinitionException(Exception): pass
class TokenizeFailException(Exception): pass

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
            raise TokenizeFailException("Cannot match token")
        
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

    def add_rule(self,name,body,tokenizer=None,value=None):
        self.rules[name] = {'body':body,'tokenizer':tokenizer,'value':value}
    
    def parse(self,text):
        if 'start' not in self.rules:
            raise ParseDefinitionException("There must be a special top rule named \'start\'")
        if not self.rules['start']['tokenizer']:
            raise ParseDefinitionException("\'start\' rule must specify a tokenizer")
        tree,offset = self.parse_rule('start',text,0,tokenizer=self.rules['start']['tokenizer'])
        offset = self.rules['start']['tokenizer'].strip_whitespace(text,offset)
        if offset != len(text):
            raise ParseFailException(f"Extra input found after program: {text[offset:]}")
        return tree

    def parse_rule(self,rule,text,offset,tokenizer=None):
        if rule not in self.rules:
            raise ParseDefinitionException("Parse error: Rule {rule} not in rules")

        for pattern in self.rules[rule]['body']:
            node = Node(rule,self.rules[rule]['value'])
            saved_offset = offset
            matched = False
            try:
                for element in pattern:
                    if element in tokenizer.tokens:
                        try:
                            token,offset = tokenizer.next_token(element,text,offset)
                            node.add_child(token)
                        except TokenizeFailException:
                            raise ParseFailException(f"Did not match token {element} at offset {offset}")
                    else:
                        raise ParseFailException(f"Unknown token at offset {offset}")
                break   # Got a complete match, so we are done!
            except ParseFailException:
                offset = saved_offset

            else:
                raise ParseFailException(f"Could not match pattern {pattern}")
            
        return node,offset
        
