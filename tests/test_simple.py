"""
A very simple grammar with no brackets.
"""
import pytest
from oreo import Tokenizer,Parser,ParseFailException


@pytest.fixture(name="simple_addition_parser")
def fixture_simple_addition_parser():
    "Simple grammar"
    tok = Tokenizer()
    tok.add_token('NUMBER','-?[0-9]+',int)
    tok.add_token('PLUS','\\+')
    tok.add_token('MINUS','\\-')

    par = Parser()
    par.add_rule('start',[
        (['NUMBER','PLUS','NUMBER'], lambda a,b,c: a.walk()+c.walk()),
        (['NUMBER','MINUS','NUMBER'],lambda a,b,c: a.walk()-c.walk()),
    ], tokenizer=tok)

    return par

def test_simple_addition(simple_addition_parser):
    "Test addition"
    assert simple_addition_parser.parse('2 + 1').walk() == 3

def test_simple_subtraction(simple_addition_parser):
    "Test subtraction"
    assert simple_addition_parser.parse('2 - 1').walk() == 1

def test_bad_input(simple_addition_parser):
    "Test failure to parse with bad input"
    with pytest.raises(ParseFailException):
        simple_addition_parser.parse('+ 1')

def test_bad_token(simple_addition_parser):
    "Test failure to parse with bad token"
    with pytest.raises(ParseFailException):
        simple_addition_parser.parse('fred + 1')

def test_extra_input(simple_addition_parser):
    "Another parse failure with bad input"
    with pytest.raises(ParseFailException):
        simple_addition_parser.parse('1 + 1 + 1')

def test_trailing_whitespace(simple_addition_parser):
    "Make sure we can handle trailing whitespace"
    assert simple_addition_parser.parse('2 + 1  ').walk() == 3
