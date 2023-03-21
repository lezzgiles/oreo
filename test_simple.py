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
        (['NUMBER','PLUS','NUMBER'], lambda a,b,c: a.walk()+c.walk()),
        (['NUMBER','MINUS','NUMBER'],lambda a,b,c: a.walk()-c.walk()),
    ], tokenizer=t)

    return p

def test_simple_addition(simple_addition_parser):
    assert simple_addition_parser.parse('2 + 1').walk() == 3

def test_simple_subtraction(simple_addition_parser):
    assert simple_addition_parser.parse('2 - 1').walk() == 1

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
    assert simple_addition_parser.parse('2 + 1  ').walk() == 3

