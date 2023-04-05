"""
Defines a mini-language with variables, simple arithmetic expressions, comparisons == and !=,
if-statements and while-statements using braces for the dependent blocks, and
statements terminated by ;
The final value of the program is the value of the variable 'result'.
"""

import pytest
from oreo import Tokenizer,Parser


#######################################
# Utility functions for the walk() functions

def setvar(ctx,sym,value):
    "Set a variable in the context"
    ctx[sym] = value

def getvar(ctx,sym):
    "Get a variable from the context"
    return ctx[sym]

def if_cond(ctx,condition,block):
    "Handle an if-statement"
    if condition.walk(ctx):
        for item in block:
            item.walk(ctx)

def while_cond(ctx,condition,block):
    "Handle a while-statement"
    while condition.walk(ctx):
        for item in block:
            item.walk(ctx)

def main_block(ctx,block):
    "Handle the top program, including pulling the final value from the 'result' variable"
    for item in block:
        item.walk(ctx)
    return ctx['result']

@pytest.fixture(name="language_parser")
def fixture_language_parser():
    "Define the parser used in the tests"
    tok = Tokenizer()
    # Arithmetic tokens
    tok.add_token('NUMBER','-?[0-9]+',lambda ctx,n: int(n))
    tok.add_token('SYMBOL','[a-zA-Z]+')
    tok.add_token('PLUS','\\+')
    tok.add_token('MINUS','-')
    tok.add_token('MULTIPLY','\\*')
    tok.add_token('DIVIDE','/')
    tok.add_token('OPEN_PAREN','\\(')
    tok.add_token('CLOSE_PAREN','\\)')
    # Comparators
    tok.add_token('ISEQUAL','==')
    tok.add_token('NOTEQUAL','!=')
    # Control flow
    tok.add_token('IF','if')
    tok.add_token('ELSE','else')
    tok.add_token('WHILE','while')
    tok.add_token('OPENBRACE','{')
    tok.add_token('CLOSEBRACE','}')
    # Statement tokens
    tok.add_token('EQUALS','=')
    tok.add_token('PRINT','print')
    tok.add_token('SEMICOLON',';')

    par = Parser()
    par.add_rule('start',[(['statement+'],main_block)],tokenizer=tok)
    par.add_rule('statement',[
        (['PRINT','add-term','SEMICOLON'], lambda ctx,a,b,c: print(b.walk(ctx))),
        (['IF','condition','OPENBRACE','statement+','CLOSEBRACE'],lambda ctx,a,b,c,d,e: if_cond(ctx,b,d)),
        (['WHILE','condition','OPENBRACE','statement+','CLOSEBRACE'],lambda ctx,a,b,c,d,e: while_cond(ctx,b,d)),
        (['SYMBOL','EQUALS','add-term','SEMICOLON'], lambda ctx,a,b,c,d: setvar(ctx,a.walk(),c.walk(ctx))),
    ])
    par.add_rule('condition',[
        (['add-term','ISEQUAL','add-term'], lambda ctx,a,b,c: a.walk(ctx) == c.walk(ctx)),
        (['add-term','NOTEQUAL','add-term'], lambda ctx,a,b,c: a.walk(ctx) != c.walk(ctx)),
    ])
    par.add_rule('add-term',[
        (['mult-term','PLUS','add-term'], lambda ctx,a,b,c: a.walk(ctx) + c.walk(ctx)),
        (['mult-term','MINUS','add-term'], lambda ctx,a,b,c: a.walk(ctx) - c.walk(ctx)),
        (['mult-term'], lambda ctx,a: a.walk(ctx)),
    ])
    par.add_rule('mult-term',[
        (['number-term','MULTIPLY','mult-term'], lambda ctx,a,b,c: a.walk(ctx) * c.walk(ctx)),
        (['number-term','DIVIDE','mult-term'], lambda ctx,a,b,c: a.walk(ctx) / c.walk(ctx)),
        (['number-term'], lambda ctx,a: a.walk(ctx)),
    ])
    par.add_rule('number-term',[
        (['OPEN_PAREN','add-term','CLOSE_PAREN'], lambda ctx,a,b,c: b.walk(ctx)),
        (['NUMBER'], lambda ctx,a: a.walk(ctx)),
        (['SYMBOL'], lambda ctx,a: ctx[a.walk()]),
    ])

    return par

def test_program(language_parser):
    "Test program with arithmetic and blocks"
    program = """
count = 1;
limit = 2;
accumulator = 1;
if count == 1 {
    limit = limit + 2;
}

while count != limit {
    accumulator = accumulator * 2;
    count = count + 1;
}
result = accumulator;
    """
    ctx = {}
    assert language_parser.parse(program,trace=True).walk(ctx) == 8
    language_parser.parse(program).dump()

def test_parsefile(language_parser):
    "Test program read from a file"
    ctx = {}
    assert language_parser.parse_file("tests/test_language/1.input").walk(ctx) == 8
    language_parser.parse_file("tests/test_language/1.input").dump()
