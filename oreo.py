#!/usr/bin/env python3

import sys
import re

class Tokenizer(object):
    def __init__(self,ignore_whitespace=True):
        self.tokens = {}
        self.ignore_whitespace = ignore_whitespace

    def add_token(self,name,regex,value=None):
        self.tokens[name] = {'regex':regex,'value':value}

    def next_token(self,name,text,offset):
        if self.ignore_whitespace:
            m = re.match('\s+',text[offset:])
            if m:
                offset += len(m.group())
        m = re.match(self.tokens[name]['regex'],text[offset:])
        if m:
            offset += len(m.group())
            return Token(name,m.group(),self.tokens[name]['value']),offset


class Token(object):
    def __init__(self,token,body,value):
        self.token = token
        self.body = body
        self.value_function = value

    def value(self):
        if self.value:
            return self.value_function(self.body)
        else:
            return self.body
        
class Node(object):
    def __init__(self,rule,value):
        self.rule = rule
        self.children = []
        self.value_function = value

    def add_child(self,child):
        self.children.append(child)

    def value(self):
        return self.value_function(*self.children)

class Parser(object):
    def __init__(self):
        self.rules = {}

    def add_rule(self,name,body,tokenizer=None,value=None):
        self.rules[name] = {'body':body,'tokenizer':tokenizer,'value':value}
    
    def parse(self,text):
        if 'start' not in self.rules:
            sys.exit(f"Parse error: There must be a special top rule named \'start\'")
        if not self.rules['start']['tokenizer']:
            sys.exit(f"Parse error: \'start\' rule must specify a tokenizer")
        return self.parse_rule('start',text,0,tokenizer=self.rules['start']['tokenizer'])

    def parse_rule(self,rule,text,offset,tokenizer=None):
        if rule not in self.rules:
            sys.exit(f"Parse error: Rule {rule} not in rules")

        node = Node(rule,self.rules[rule]['value'])
        for element in self.rules[rule]['body']:
            if element in tokenizer.tokens:
                token,offset = tokenizer.next_token(element,text,offset)
                node.add_child(token)

        return node
        
if __name__ == "__main__":
    t = Tokenizer()
    t.add_token('NUMBER','-?[0-9]+',lambda n: int(n))
    t.add_token('PLUS','\+')

    p = Parser()
    p.add_rule('start',['NUMBER','PLUS','NUMBER'],tokenizer=t,value=lambda a,b,c: a.value()+c.value())

    print(p.parse('2 + 1').value())