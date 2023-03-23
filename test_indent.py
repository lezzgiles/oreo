from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException
from functools import reduce
import pytest

@pytest.fixture
def simple_parser():
    t = Tokenizer()
    t.add_token('START','start')
    t.add_token('END','end')
    t.use_indent_tokens('INDENT','OUTDENT')

    p = Parser()
    p.add_rule('start',[(['START','INDENT','END'],lambda a,b,c: True)],t)

    return p

def test_simple_indent(simple_parser):
    p = """
start
    end
    """
    assert simple_parser.parse(p).walk()
    
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
    t.add_token('ADD_BLOCK_START','add:')
    t.add_token('MULTIPLY_BLOCK_START','multiply:')
    t.use_indent_tokens('INDENT','OUTDENT')

    p = Parser()
    
    p.add_rule('start',[(['add-block+'],lambda ctx,a: sum([ i.walk(ctx) for i in a ]) )],tokenizer=t)

    p.add_rule('add-block',[
        (['ADD_BLOCK_START','INDENT','multiply-block+','OUTDENT'], lambda ctx,a: sum([ i.walk(ctx) for i in a ]))
    ])
    p.add_rule('multiply-block',[
        (['MULTIPLY_BLOCK_START','INDENT','add-term+','OUTDENT'], lambda ctx,a: reduce(lambda x,y:x*y,[ i.walk(ctx) for i in a ]) )
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
        (['SYMBOL'], lambda ctx,a: get_value(ctx,a.walk(ctx))),
    ])
    p.add_rule('statement',[
        (['VALUE','add-term','SEMICOLON'], lambda ctx,a,b,c: b.walk(ctx)),
        (['SYMBOL','EQUALS','add-term','SEMICOLON'], lambda ctx,a,b,c,d: set_value(ctx,a.walk(ctx), c.walk(ctx))),
    ])

    return p

def test_indent_output(language_parser):
    context = {}
    p = """
add:
  multiply:
    1 2 3
  multiply:
    2 3 4
    """
    assert (language_parser.parse(p).walk(context))[-1] == 30
