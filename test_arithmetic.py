"""
Test for grammar that understands simple arithmetic expressions
"""
import pytest
from oreo import Tokenizer,Parser

@pytest.fixture(name="arithmetic_parser")
def fixture_arithmetic_parser():
    "Grammar for simple arithmetic expressions"
    tok = Tokenizer()
    tok.add_token('NUMBER','-?[0-9]+',int)
    tok.add_token('PLUS','\\+')
    tok.add_token('MINUS','-')
    tok.add_token('MULTIPLY','\\*')
    tok.add_token('DIVIDE','/')
    tok.add_token('OPEN_PAREN','\\(')
    tok.add_token('CLOSE_PAREN','\\)')

    par = Parser()
    par.add_rule('start',[(['add-term'], lambda a: a.walk())],tokenizer=tok)
    par.add_rule('add-term',[
        (['mult-term','PLUS','add-term'], lambda a,b,c: a.walk() + c.walk()),
        (['mult-term','MINUS','add-term'], lambda a,b,c: a.walk() - c.walk()),
        (['mult-term'], lambda a: a.walk()),
    ])
    par.add_rule('mult-term',[
        (['number-term','MULTIPLY','mult-term'], lambda a,b,c: a.walk() * c.walk()),
        (['number-term','DIVIDE','mult-term'], lambda a,b,c: a.walk() / c.walk()),
        (['number-term'], lambda a: a.walk()),
    ])
    par.add_rule('number-term',[
        (['OPEN_PAREN','add-term','CLOSE_PAREN'], lambda a,b,c: b.walk()),
        (['NUMBER'], lambda a: a.walk()),
    ])

    return par

def test_arith(arithmetic_parser):
    "Test simple expression with no brackets"
    assert arithmetic_parser.parse('2 + 1').walk() == 3

def test_arith_brackets(arithmetic_parser):
    "Test with brackets"
    assert arithmetic_parser.parse('(2 + 1) * 3').walk() == 9

def test_arith_divide(arithmetic_parser):
    "Test with no whitespace between some tokens"
    assert arithmetic_parser.parse('(3 - 1)/2').walk() == 1
