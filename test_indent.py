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
    t.use_indent_tokens('INDENT','OUTDENT',tabsize=4)

    p = Parser()
    
    p.add_rule('start',[(['add-block+'],lambda ctx,a: sum([ i.walk(ctx) for i in a ]) )],tokenizer=t)

    p.add_rule('add-block',[
        (['ADD_BLOCK_START','INDENT','multiply-block+','OUTDENT'], lambda ctx,a,b,c,d: sum([ i.walk(ctx) for i in c ]))
    ])
    p.add_rule('multiply-block',[
        (['MULTIPLY_BLOCK_START','INDENT','add-term+','OUTDENT'], lambda ctx,a,b,c,d: reduce(lambda x,y:x*y,[ i.walk(ctx) for i in c ]) )
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
        (['SYMBOL'], lambda ctx,a: ctx[a.walk(ctx)]),
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
    assert (language_parser.parse(p,trace=True).walk(context)) == 30

def test_tab(language_parser):
    context = {}
    p = """
add:
  multiply:
\t1 2 3
  multiply:
    2 3 4
"""
    assert (language_parser.parse(p,trace=True).walk(context)) == 30


# Small subset of yaml, supporting just lists and dictionaries, using the simplest syntax.
# Used to test subindents
@pytest.fixture
def yaml_subset_parser():
    t = Tokenizer()
    t.add_token('NUMBER','-?[0-9]+',lambda n: int(n))
    t.add_token('STRING','[a-zA-Z]+')
    t.add_token('COLON',':')
    t.add_token('BULLET','-')
    t.use_indent_tokens('INDENT','OUTDENT',tabsize=4,inline_indents=True)
    
    p = Parser()

    p.add_rule('start',[(['construct'],lambda a: a.walk())],tokenizer=t)
    p.add_rule('construct',[
        (['item+'],lambda a: [ i.walk() for i in a ]),
        (['keyvalue+'],lambda a: dict([i.walk() for i in a])),
    ])
    p.add_rule('item',[
        (['BULLET','INDENT','construct','OUTDENT'],lambda a,b,c,d: c.walk()),
        (['BULLET','INDENT','NUMBER',   'OUTDENT'],lambda a,b,c,d: c.walk()),
        (['BULLET','INDENT','STRING',   'OUTDENT'],lambda a,b,c,d: c.walk()),
    ])
    p.add_rule('keyvalue',[
        (['STRING','COLON','INDENT','construct','OUTDENT'],lambda a,b,c,d,e: (a.walk(),d.walk())),
        (['STRING','COLON','INDENT','NUMBER',   'OUTDENT'],lambda a,b,c,d,e: (a.walk(),d.walk())),
        (['STRING','COLON','INDENT','STRING',   'OUTDENT'],lambda a,b,c,d,e: (a.walk(),d.walk())),
    ])

    return p
    
def test_subindent(yaml_subset_parser):
    p = """
- alpha: 1
  beta: 2
  gamma: 3
- a: 4
  b: 5
  c: 6
"""
    assert(yaml_subset_parser.parse(p,trace=True).walk())[0]['beta'] == 2
