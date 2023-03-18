from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException

import pytest

@pytest.fixture
def arithmetic_parser():
    t = Tokenizer()
    t.add_token('NUMBER','-?[0-9]+',lambda n: int(n))
    t.add_token('PLUS','\+')
    t.add_token('MINUS','-')
    t.add_token('MULTIPLY','\*')
    t.add_token('DIVIDE','/')
    t.add_token('OPEN_PAREN','\(')
    t.add_token('CLOSE_PAREN','\)')

    p = Parser()
    p.add_rule('start',[(['add-term'], lambda a: a.value())],tokenizer=t)
    p.add_rule('add-term',[
        (['mult-term','PLUS','add-term'], lambda a,b,c: a.value() + c.value()),
        (['mult-term','MINUS','add-term'], lambda a,b,c: a.value() - c.value()),
        (['mult-term'], lambda a: a.value()),
    ])
    p.add_rule('mult-term',[
        (['number-term','MULTIPLY','mult-term'], lambda a,b,c: a.value() + c.value()),
        (['number-term','DIVIDE','mult-term'], lambda a,b,c: a.value() + c.value()),
        (['number-term'], lambda a: a.value()),
    ])
    p.add_rule('number-term',[
        (['OPEN_PAREN','add-term','CLOSE_PAREN'], lambda a,b,c: b.value()),
        (['NUMBER'], lambda a: a.value()),
    ])

    return p

def test_arith(arithmetic_parser):
    assert arithmetic_parser.parse('2 + 1').value() == 3
