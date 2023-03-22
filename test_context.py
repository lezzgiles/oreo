from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException

import re

import pytest

def set_value(ctx,symbol,walk):
    ctx[symbol] = walk

def get_value(ctx,symbol):
    if symbol not in ctx:
        raise NameError(f"Symbol {symbol} not set!")
    return ctx[symbol]

@pytest.fixture
def language_parser():
    t = Tokenizer()
    t.add_token('NUMBER','-?[0-9]+',lambda ctx,n: int(n))
    t.add_token('PLUS','\+')
    t.add_token('MINUS','-')
    t.add_token('MULTIPLY','\*')
    t.add_token('DIVIDE','/')
    t.add_token('OPEN_PAREN','\(')
    t.add_token('CLOSE_PAREN','\)')
    t.add_token('EQUALS','=')
    t.add_token('VALUE','value')
    t.add_token('SYMBOL','[a-zA-Z]+')
    t.add_token('SEMICOLON',';')
    t.add_comment_style('/\*.*?\*/',re.DOTALL)
    t.add_comment_style('#.*$',re.MULTILINE)

    p = Parser()
    p.add_rule('start',[(['statement+'],lambda ctx,a: [ i.walk(ctx) for i in a ] )],tokenizer=t)
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
        (['SYMBOL'], lambda ctx,a: get_value(ctx,a.walk(ctx))),
    ])
    p.add_rule('statement',[
        (['VALUE','add-term','SEMICOLON'], lambda ctx,a,b,c: b.walk(ctx)),
        (['SYMBOL','EQUALS','add-term','SEMICOLON'], lambda ctx,a,b,c,d: set_value(ctx,a.walk(ctx), c.walk(ctx))),
    ])

    return p

def test_assign(language_parser):
    context = {}
    assert (language_parser.parse('a = 1 + 1; b = 2 * 3; value a+b;').walk(context))[-1] == 8


def test_comments_style_to_eol(language_parser):
    p = """
        a = 1 + 1;    # This is a comment
           b = 2 * 3;
        value a+b;
        """
    context = {}
    assert (language_parser.parse(p).walk(context))[-1] == 8

def test_comments_multiline_style(language_parser):
    p = """
        a = 1 + 1; # This is a comment
        /* And this is a
         * multiline
         * comment.
         */
        b = 2 * 3;
        value a+b;
        """
    context = {}
    assert (language_parser.parse(p).walk(context))[-1] == 8
