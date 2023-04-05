"""
Grammar for a language that supports variables.
"""
import re
import pytest
from oreo import Tokenizer,Parser


def set_value(ctx,symbol,walk):
    "Set a value in a context thing"
    ctx[symbol] = walk

def get_value(ctx,symbol):
    "Get the value from a context thing"
    if symbol not in ctx:
        raise NameError(f"Symbol {symbol} not set!")
    return ctx[symbol]

@pytest.fixture(name="language_parser")
def fixture_language_parser():
    "Grammar definition for the tests"
    tok = Tokenizer()
    tok.add_token('NUMBER','-?[0-9]+',lambda ctx,n: int(n))
    tok.add_token('PLUS','\\+')
    tok.add_token('MINUS','-')
    tok.add_token('MULTIPLY','\\*')
    tok.add_token('DIVIDE','/')
    tok.add_token('OPEN_PAREN','\\(')
    tok.add_token('CLOSE_PAREN','\\)')
    tok.add_token('EQUALS','=')
    tok.add_token('VALUE','value')
    tok.add_token('SYMBOL','[a-zA-Z]+')
    tok.add_token('SEMICOLON',';')
    tok.add_comment_style('/\\*.*?\\*/',re.DOTALL)
    tok.add_comment_style('#.*$',re.MULTILINE)

    par = Parser()
    par.add_rule('start',[(['statement+'],lambda ctx,a: [ i.walk(ctx) for i in a ] )],tokenizer=tok)
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
        (['SYMBOL'], lambda ctx,a: get_value(ctx,a.walk(ctx))),
    ])
    par.add_rule('statement',[
        (['VALUE','add-term','SEMICOLON'], lambda ctx,a,b,c: b.walk(ctx)),
        (['SYMBOL','EQUALS','add-term','SEMICOLON'], lambda ctx,a,b,c,d: set_value(ctx,a.walk(ctx), c.walk(ctx))),
    ])

    return par

def test_assign(language_parser):
    "Test assignment to stuff in a context"
    context = {}
    assert (language_parser.parse('a = 1 + 1; b = 2 * 3; value a+b;').walk(context))[-1] == 8


def test_comments_style_to_eol(language_parser):
    "Test with indents"
    program = """
        a = 1 + 1;    # This is a comment
           b = 2 * 3;
        value a+b;
        """
    context = {}
    assert (language_parser.parse(program).walk(context))[-1] == 8

def test_comments_multiline_style(language_parser):
    "Test indents and comments"
    program = """
        a = 1 + 1; # This is a comment
        /* And this is a
         * multiline
         * comment.
         */
        b = 2 * 3;
        value a+b;
        """
    context = {}
    assert (language_parser.parse(program).walk(context))[-1] == 8
