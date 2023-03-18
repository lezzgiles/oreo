from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException

import pytest

@pytest.fixture
def simple_addition_parser():
    t = Tokenizer()
    t.add_token('NUMBER','-?[0-9]+',lambda n: int(n))
    t.add_token('PLUS','\+')
    t.add_token('MINUS','\-')

    p = Parser()
    p.add_rule('start',[
        (['NUMBER','PLUS','NUMBER'], lambda a,b,c: a.value()+c.value()),
        (['NUMBER','MINUS','NUMBER'],lambda a,b,c: a.value()-c.value()),
    ], tokenizer=t)

    return p

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

def test_simple_addition(simple_addition_parser):
    assert simple_addition_parser.parse('2 + 1').value() == 3

def test_simple_subtraction(simple_addition_parser):
    assert simple_addition_parser.parse('2 - 1').value() == 1

def test_bad_input(simple_addition_parser):
    with pytest.raises(ParseFailException):
        simple_addition_parser.parse('+ 1')

def test_bad_token(simple_addition_parser):
    with pytest.raises(ParseFailException):
        simple_addition_parser.parse('fred + 1')

def test_extra_input(simple_addition_parser):
    with pytest.raises(ParseFailException):
        simple_addition_parser.parse('1 + 1 + 1')

def test_trailing_whitespace(simple_addition_parser):
    assert simple_addition_parser.parse('2 + 1  ').value() == 3

def test_arith(arithmetic_parser):
    assert arithmetic_parser.parse('2 + 1').value() == 3
