"""
Test language that uses indents for block structure, like python.
"""
from functools import reduce
import pytest
from oreo import Tokenizer,Parser

@pytest.fixture(name="simple_parser")
def fixture_simple_parser():
    "Simple grammar with indents"
    tok = Tokenizer()
    tok.add_token('START','start')
    tok.add_token('END','end')
    tok.use_indent_tokens('INDENT','OUTDENT')

    par = Parser()
    par.add_rule('start',[(['START','INDENT','END'],lambda a,b,c: True)],tok)

    return par

def test_simple_indent(simple_parser):
    "First test is a very simple indent thing"
    prog = """
start
    end
    """
    assert simple_parser.parse(prog).walk()

@pytest.fixture(name="language_parser")
def fixture_language_parser():
    "More complex grammar with blocks"
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
    tok.add_token('ADD_BLOCK_START','add:')
    tok.add_token('MULTIPLY_BLOCK_START','multiply:')
    tok.use_indent_tokens('INDENT','OUTDENT',tabsize=4)

    par = Parser()

    par.add_rule('start',[(['add-block+'],lambda ctx,a: sum([ i.walk(ctx) for i in a ]) )],tokenizer=tok)

    par.add_rule('add-block',[
        (['ADD_BLOCK_START','INDENT','multiply-block+','OUTDENT'], lambda ctx,a,b,c,d: sum([ i.walk(ctx) for i in c ]))
    ])
    par.add_rule('multiply-block',[
        (['MULTIPLY_BLOCK_START','INDENT','add-term+','OUTDENT'], lambda ctx,a,b,c,d: reduce(lambda x,y:x*y,[ i.walk(ctx) for i in c ]) )
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
        (['SYMBOL'], lambda ctx,a: ctx[a.walk(ctx)]),
    ])

    return par

def test_indent_output(language_parser):
    "Test structures with mltiple levels of indent"
    context = {}
    prog = """
add:
  multiply:
    1 2 3
  multiply:
    2 3 4
"""
    assert language_parser.parse(prog,trace=True).walk(context) == 30

def test_tab(language_parser):
    "Test a tab character in the input"
    context = {}
    prog = """
add:
  multiply:
\t1 2 3
  multiply:
    2 3 4
"""
    assert language_parser.parse(prog,trace=True).walk(context) == 30


@pytest.fixture(name="yaml_subset_parser")
def fixture_yaml_subset_parser():
    """
    Small subset of yaml, supporting just lists and dictionaries, using the simplest syntax.
    Used to test subindents
    """
    tok = Tokenizer()
    tok.add_token('NUMBER','-?[0-9]+',int)
    tok.add_token('STRING','[a-zA-Z]+')
    tok.add_token('COLON',':')
    tok.add_token('BULLET','-')
    tok.use_indent_tokens('INDENT','OUTDENT',tabsize=4,inline_indents=True)

    par = Parser()

    par.add_rule('start',[(['construct'],lambda a: a.walk())],tokenizer=tok)
    par.add_rule('construct',[
        (['item+'],lambda a: [ i.walk() for i in a ]),
        (['keyvalue+'],lambda a: dict([i.walk() for i in a])),
    ])
    par.add_rule('item',[
        (['BULLET','INDENT','construct','OUTDENT'],lambda a,b,c,d: c.walk()),
        (['BULLET','INDENT','NUMBER',   'OUTDENT'],lambda a,b,c,d: c.walk()),
        (['BULLET','INDENT','STRING',   'OUTDENT'],lambda a,b,c,d: c.walk()),
    ])
    par.add_rule('keyvalue',[
        (['STRING','COLON','INDENT','construct','OUTDENT'],lambda a,b,c,d,e: (a.walk(),d.walk())),
        (['STRING','COLON','INDENT','NUMBER',   'OUTDENT'],lambda a,b,c,d,e: (a.walk(),d.walk())),
        (['STRING','COLON','INDENT','STRING',   'OUTDENT'],lambda a,b,c,d,e: (a.walk(),d.walk())),
    ])

    return par

def test_subindent(yaml_subset_parser):
    "Test subindents, like in yaml"
    prog = """
- alpha: 1
  beta: 2
  gamma: 3
- a: 4
  b: 5
  c: 6
"""
    assert yaml_subset_parser.parse(prog,trace=True).walk()[0]['beta'] == 2
