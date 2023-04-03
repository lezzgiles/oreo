from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException

import pytest

# Defines a mini-language with variables, simple arithmetic expressions, comparisons == and !=,
# if-statements and while-statements using braces for the dependent blocks, and
# statements terminated by ;
# The final value of the program is the value of the variable 'result'.

#######################################
# Utility functions for the walk() functions

def set(ctx,sym,value):
    "Set a variable in the context"
    ctx[sym] = value

def get(ctx,sym):
    "Get a variable from the context"
    return ctx[sym]

def if_cond(ctx,condition,block):
    "Handle an if-statement"
    if condition.walk(ctx):
        for b in block:
            b.walk(ctx)

def while_cond(ctx,condition,block):
    "Handle a while-statement"
    while condition.walk(ctx):
        for b in block:
            b.walk(ctx)

def main_block(ctx,block):
    "Handle the top program, including pulling the final value from the 'result' variable"
    for b in block:
        b.walk(ctx)
    return ctx['result']

@pytest.fixture
def language_parser():
    t = Tokenizer()
    # Arithmetic tokens
    t.add_token('NUMBER','-?[0-9]+',lambda ctx,n: int(n))
    t.add_token('SYMBOL','[a-zA-Z]+')
    t.add_token('PLUS','\+')
    t.add_token('MINUS','-')
    t.add_token('MULTIPLY','\*')
    t.add_token('DIVIDE','/')
    t.add_token('OPEN_PAREN','\(')
    t.add_token('CLOSE_PAREN','\)')
    # Comparators
    t.add_token('ISEQUAL','==')
    t.add_token('NOTEQUAL','!=')
    # Control flow
    t.add_token('IF','if')
    t.add_token('ELSE','else')
    t.add_token('WHILE','while')
    t.add_token('OPENBRACE','{')
    t.add_token('CLOSEBRACE','}')
    # Statement tokens
    t.add_token('EQUALS','=')
    t.add_token('PRINT','print')
    t.add_token('SEMICOLON',';')

    p = Parser()
    p.add_rule('start',[(['statement+'],lambda ctx,a: main_block(ctx,a))],tokenizer=t)
    p.add_rule('statement',[
        (['PRINT','add-term','SEMICOLON'], lambda ctx,a,b,c: print(b.walk(ctx))),
        (['IF','condition','OPENBRACE','statement+','CLOSEBRACE'],lambda ctx,a,b,c,d,e: if_cond(ctx,b,d)),
        (['WHILE','condition','OPENBRACE','statement+','CLOSEBRACE'],lambda ctx,a,b,c,d,e: while_cond(ctx,b,d)),
        (['SYMBOL','EQUALS','add-term','SEMICOLON'], lambda ctx,a,b,c,d: set(ctx,a.walk(),c.walk(ctx))),
    ])
    p.add_rule('condition',[
        (['add-term','ISEQUAL','add-term'], lambda ctx,a,b,c: a.walk(ctx) == c.walk(ctx)),
        (['add-term','NOTEQUAL','add-term'], lambda ctx,a,b,c: a.walk(ctx) != c.walk(ctx)),
    ])
    p.add_rule('add-term',[
        (['mult-term','PLUS','add-term'], lambda ctx,a,b,c: a.walk(ctx) + c.walk(ctx)),
        (['mult-term','MINUS','add-term'], lambda ctx,a,b,c: a.walk(ctx) - c.walk(ctx)),
        (['mult-term'], lambda ctx,a: a.walk(ctx)),
    ])
    p.add_rule('mult-term',[
        (['number-term','MULTIPLY','mult-term'], lambda ctx,a,b,c: a.walk(ctx) * c.walk(ctx)),
        (['number-term','DIVIDE','mult-term'], lambda ctx,a,b,c: a.walk(ctx) / c.walk(ctx)),
        (['number-term'], lambda ctx,a: a.walk(ctx)),
    ])
    p.add_rule('number-term',[
        (['OPEN_PAREN','add-term','CLOSE_PAREN'], lambda ctx,a,b,c: b.walk(ctx)),
        (['NUMBER'], lambda ctx,a: a.walk(ctx)),
        (['SYMBOL'], lambda ctx,a: ctx[a.walk()]),
    ])
                        
    return p

def test_program(language_parser):
    p = """
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
    assert(language_parser.parse(p,trace=True).walk(ctx) == 8)
    language_parser.parse(p).dump()

def test_parsefile(language_parser):
    ctx = {}
    assert(language_parser.parse_file("test_language/1.input").walk(ctx) == 8)
