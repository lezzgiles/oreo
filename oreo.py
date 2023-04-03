#!/usr/bin/env python3
"""
Provides the Tokenizer and Parser classes that will take
a grammar and generate a walkable tree of Node and Token objects.
"""
from copy import deepcopy,copy

import sys
import re

class ParseFailException(Exception):
    "Failed to parse input"

class ParseDefinitionException(Exception):
    "Something wrong with the grammar definition"

class LocationTracker:
    "Track current location in input stream; allow for backtracking"
    def __init__(self, text:str, filename:str, offset:int = 0, column:int = 0, indents:int = None):
        self.all_text = text
        self.offset = offset
        self.column = column
        self.last_indent = 0
        if indents:
            self.indents = indents
        else:
            self.indents = [0]
        self.highwatermark = 0
        self.filename = filename
        self.linenumber = 0

    def text(self) -> str:
        "Simply return the text from the current offset to the end of input"
        return self.all_text[self.offset:]

    def match(self,regex:str,tabsize:int=0,flags:int=0) -> str:
        """
        If regex matches text, return the match and
        move up the location; otherwise raise exception.
        """
        match = re.match(regex,self.text(),flags)
        if match:
            self.offset += len(match.group())
            newline_match = re.search('\n$',match.group())
            if newline_match:
                self.linenumber += 1
                self.column = 0
            else:
                self.column += len(match.group())+(match.group().count("\t")*(tabsize-1))
            return match.group()
        else:
            raise ParseFailException

    def match_bool(self,regex:str,tabsize:int=0,flags:int=0) -> bool:
        """
        If regex matches text, return True and move up
        the location; otherwise return False
        """
        try:
            self.match(regex,tabsize,flags)
        except ParseFailException:
            return False
        return True

    def strip_trailing_whitespace(self,tabsize:int=0) -> bool:
        "Remove whitespace up to end-of-line"
        if self.match_bool('[ \t]*\n',tabsize):
            return True
        else:
            return False

    def strip_other_whitespace(self,tabsize:int) -> bool:
        "Remove whitespace inside a line, possibly at the beginning of a line"
        try:
            starting_column = self.column
            spaces = self.match('[ \t]*',tabsize)
            if starting_column == 0:
                self.last_indent = self.column
            if len(spaces) > 0:
                return True
            else:
                return False
        except ParseFailException:
            return False

    def backtrack(self,location:'LocationTracker'):
        "Revert to an earlier location"
        self.all_text = location.all_text
        self.offset = location.offset
        self.filename = location.filename
        self.linenumber = location.linenumber
        self.column = location.column
        self.last_indent = location.last_indent
        self.indents = copy(location.indents)
        self.highwatermark = location.highwatermark

class Tokenizer:
    """
    Tokenizer takes a list of token definitions and will determine if text matches a specific token.
    """
    def __init__(self,ignore_whitespace:bool=True):
        self.tokens = {}
        self.ignore_whitespace = ignore_whitespace
        self.comment_styles = []
        self.indent_tokens = ()
        self.tabsize = 0
        self.inline_indents = False

    def add_token(self,name:str,regex:str,walk:callable=None):
        "User-visible method to add a token to the tokenizer"
        self.tokens[name] = {'regex':regex,'walk':walk}

    def add_comment_style(self,regex:str,flags:int=0):
        "User-visible method to add a regex that defines a comment style"
        self.comment_styles.append((regex,flags))

    def use_indent_tokens(self,indent_token:str,outdent_token:str,tabsize:int=0,inline_indents:bool=False):
        "User-visible method to define how indent & outdent tokens are defined"
        if not self.ignore_whitespace:
            raise ParseDefinitionException("Cannot use indent/outdent tokens and not ignore_whitespace")
        self.indent_tokens = (indent_token,outdent_token)
        self.tabsize = tabsize
        self.inline_indents = inline_indents

    def next_token(self,name:str,location:LocationTracker) -> 'Token':
        "Return the next token if it matches 'name'"
        self.strip_whitespace_and_comments(location)
        location.highwatermark = location.offset
        token_start_filename = location.filename
        token_start_linenumber = location.linenumber
        token_start_column = location.column

        # Now we've stripped everything, comments and spaces, up to
        # the next real thing, so look at the indent level.  We look
        # at the level before every token, but it won't change in the same line
        if self.indent_tokens:
            current_indent = location.last_indent

            if current_indent > location.indents[-1]:
                # Indent increased
                location.indents.append(current_indent)
                if name == self.indent_tokens[0]:
                    return Token(self.indent_tokens[0],current_indent,token_start_filename,token_start_linenumber,token_start_column)
                else:
                    raise ParseFailException("Mismatch: expecting {name} but got {self.indent_tokens[0]}")

            elif not current_indent in location.indents:
                raise ParseFailException("Outdent to non-matching indentation level")

            elif current_indent < location.indents[-1]:
                # Indent decreased
                location.indents.pop()
                if name == self.indent_tokens[1]:
                    return Token(self.indent_tokens[1],current_indent,token_start_filename,token_start_linenumber,token_start_column)
                else:
                    raise ParseFailException("Mismatch: expecting {name} but got {self.indent_tokens[1]}")

        # If we are expecting an INDENT then it could be a same-line indent
        if self.indent_tokens and name == self.indent_tokens[0] and self.inline_indents:
            current_indent = location.column
            location.indents.append(current_indent)
            location.last_indent = current_indent
            return Token(self.indent_tokens[0],current_indent,token_start_filename,token_start_linenumber,token_start_column)

        # If we are expecting the INDENT or OUTDENT tokens but didn't see one, that's an error
        if name in self.indent_tokens:
            raise ParseFailException

        value = location.match(self.tokens[name]['regex'],self.tabsize)
        location.highwatermark = location.offset
        return Token(name,value,token_start_filename,token_start_linenumber,token_start_column,self.tokens[name]['walk'])

    def strip_whitespace_and_comments(self,location:LocationTracker):
        "Repeatedly try removing whitespace and comments"
        modified = True
        while modified:
            modified = False
            if self.ignore_whitespace:
                # Trailing whitespace
                if location.strip_trailing_whitespace():
                    modified = True
                # Non-trailing whitespace
                if location.strip_other_whitespace(self.tabsize):
                    modified = True

            for (comment_style,flags) in self.comment_styles:
                if location.match_bool(comment_style, self.tabsize, flags):
                    modified = True

class Token:
    """
    A token in the language, generated by Tokenizer
    """
    def __init__(self,token:str,body,filename:str,linenumber:int,column:int,walk_function:callable=None):
        self.token = token
        self.body = body
        self.filename = filename
        self.linenumber = linenumber
        self.column = column
        self.walk_function = walk_function

    def walk(self,*context):
        "Call the walk() function defined for this token; if no walk() defined then just return the token value"
        if self.walk_function:
            try:
                return self.walk_function(*context,self.body)
            except TypeError as exc:
                raise ParseDefinitionException(f"walk() function for {self.token} called with wrong number of arguments - did you forget to pass in the context?") from exc
        else:
            return self.body

    def dump(self,indent:str=""):
        "Dump the Token contents"
        print(f"{indent}- {self.token} = \"{self.body}\"; file {self.filename}:{self.linenumber}:{self.column}")


class Node:
    """
    A node in the language grammar, also the root of a tree or sub-tree.
    """
    def __init__(self,rule:str,walk_function:callable):
        self.rule = rule
        self.children = []
        self.walk_function = walk_function

    def add_child(self,child:'Node'):
        "Just add a child Token or Node to the tree"
        self.children.append(child)

    def walk(self,*context):
        "Call the walk() function defined for this node in the grammar."
        try:
            return self.walk_function(*context,*self.children)
        except TypeError as exc:
            raise ParseDefinitionException(f"walk() function for {self.rule} called with wrong number of arguments - did you forget to pass in the context?") from exc

    def dump(self,indent:str=""):
        "Dump the Node contents along with any children nodes"
        print(f"{indent}- {self.rule}")
        for child in self.children:
            if isinstance(child,list):
                for grandchild in child:
                    grandchild.dump(indent+"  ")
            else:
                child.dump(indent+"  ")

class Parser:
    """
    Define a grammar and tokenizer(s) used to parse input.  Provides methods to add grammar rules and to parse input.
    """
    def __init__(self):
        self.rules = {}
        self._trace = False

    def __trace(self,indent:str,message:str):
        "Print a trace message"
        if self._trace:
            print(f"{indent}{message}",file=sys.stderr)

    def add_rule(self,name:str,body,tokenizer:Tokenizer=None):
        "User-visible method to add a rule."
        if name in self.rules:
            raise ParseDefinitionException(f"Rule \"{name}\" multiply defined!")
        self.rules[name] = {'body':body,'tokenizer':tokenizer}

    def parse(self,text:str,trace:bool=False,filename:str="Input") -> Node:
        "User-visible method to parse input"
        self._trace = trace

        if 'start' not in self.rules:
            raise ParseDefinitionException("There must be a special top rule named \'start\'")
        if not self.rules['start']['tokenizer']:
            raise ParseDefinitionException("\'start\' rule must specify a tokenizer")
        location = LocationTracker(text,filename)
        try:
            tree = self.__parse_rule('start',location,tokenizer=self.rules['start']['tokenizer'],indent="")
        except ParseFailException as exc:
            raise ParseFailException(f"Failed to parse: Failed around: {location.all_text[location.highwatermark:]}") from exc

        self.rules['start']['tokenizer'].strip_whitespace_and_comments(location)
        if location.text() != "":
            raise ParseFailException(f"Extra input found after input: {location.text()}")
        return tree

    def parse_file(self,filename:str,trace:bool=False) -> Node:
        """
        Parse the contents of a file.
        Need to read in the whole file because we backtrack a lot during the parsing/tokenizing
        """

        with open(filename, encoding='utf-8') as input_file:
            body = input_file.read()

        return self.parse(body,trace,filename=filename)

    @staticmethod
    def __expand_grammar_item(element:str):
        """
        Looks at an element in the grammar, e.g. this+, and returns the element name
        'this' and the minimum and maximum number of instances, for example:
        'this+' => 'this',(1,None)
        'this*' => 'this',(0,None)
        'this?' => 'this',(0,1)
        'this' => 'this',()
        """
        match = re.match('([a-zA-Z0-9_-]+)(.*)',element)
        if not match:
            raise ParseDefinitionException(f"Parse Error: token {element} misformed")
        if match.group(2) == '+':
            matches = ( 1,None )
        elif match.group(2) == '*':
            matches = ( 0,None )
        elif match.group(2) == '?':
            matches = ( 0,1 )
        elif match.group(2) == '':
            matches = ()

        return match.group(1),matches

    def __parse_element(self,element:str,location:LocationTracker,tokenizer:Tokenizer,indent:str):
        """
        Parse element, which can be a terminal or a non-terminal.
        Return a Node or a Token and an updated location, or raise ParseFailException
        """
        if element in list(tokenizer.tokens)+list(tokenizer.indent_tokens):
            tree = tokenizer.next_token(element,location)
        elif element in self.rules:
            tree = self.__parse_rule(element,location,tokenizer,indent)
        else:
            raise ParseDefinitionException(f"element {element} not defined")
        return tree

    def __parse_grammar_item(self,element:str,location:LocationTracker,tokenizer:Tokenizer,indent:str):
        """
        Parse a grammar item, which will be a Node or Token with a possible trailing modifier (+, * or ?)
        """
        elt,matches_specifiers = Parser.__expand_grammar_item(element)
        if not matches_specifiers:
            return self.__parse_element(elt,location,tokenizer,indent=indent+"  ")
        else:
            retval = []
            count = 0
            while True:
                try:
                    tree = self.__parse_element(elt,location,tokenizer,indent=indent+"  ")
                    retval.append(tree)
                except ParseFailException as exc:
                    if matches_specifiers[0] > count:
                        raise ParseFailException("Not enough terms match in list") from exc
                    break
                count += 1
                if matches_specifiers[1] and count == matches_specifiers[1]:
                    break
            return retval

    def __parse_rule(self,rule:str,location:LocationTracker,tokenizer:Tokenizer,indent:str=""):
        """
        Parse an entire rule.  This is the recursive-friendly key method for Parser.
        """
        if rule not in self.rules:
            raise ParseDefinitionException("Parse error: Rule {rule} not in rules")

        self.__trace(indent,f"Trying to expand {rule} with text {location.text()}")

        if self.rules[rule]['tokenizer']:
            tokenizer = self.rules[rule]['tokenizer']

        for pattern,walk_function in self.rules[rule]['body']:
            self.__trace(indent,f" Looking at {pattern}")
            node = Node(rule,walk_function)
            saved_location = deepcopy(location)
            try:
                for element in pattern:
                    tree = self.__parse_grammar_item(element,location,tokenizer,indent=indent+"  ")
                    self.__trace(indent,f"  Got match for {element}")
                    node.add_child(tree)
                # Got a complete match, so we are done!
                self.__trace(indent,f" Got a complete match for {pattern}")
                break
            except ParseFailException:
                self.__trace(indent,f" Failed a complete match for {pattern}")
                location.backtrack(saved_location)

        else:
            raise ParseFailException(f"Could not match pattern {pattern}")

        return node
