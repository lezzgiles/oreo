"""
Test modifiers + * ?
"""
import pytest
from oreo import Tokenizer,Parser

@pytest.fixture(name="addlist_parser")
def fixture_addlist_parser():
    "Grammar that uses all three modifiers"
    tok = Tokenizer()
    tok.add_token('NUMBER','-?[0-9]+',int)
    tok.add_token('SINGLE','single')
    tok.add_token('OPTIONAL','optional')
    tok.add_token('LONGLIST','longlist')
    tok.add_token('SHORTLIST','shortlist')

    par = Parser()
    par.add_rule('start',[
               (['SINGLE','NUMBER'], lambda a,b: b.walk()),
               (['OPTIONAL','NUMBER?'], lambda a,b: sum([i.walk() for i in b])),
               (['LONGLIST','NUMBER+'], lambda a,b: sum([i.walk() for i in b])),
               (['SHORTLIST','NUMBER*'], lambda a,b: sum([i.walk() for i in b])),
               ],tokenizer=tok)

    return par

def test_arith_optional_with(addlist_parser):
    "Test modifier ? with a thing"
    assert addlist_parser.parse('optional 1').walk() == 1

def test_arith_optional_without(addlist_parser):
    "Test modifier ? without a thing"
    assert addlist_parser.parse('optional ').walk() == 0

def test_arith_longlist(addlist_parser):
    "Test modifier +"
    assert addlist_parser.parse('longlist 2 1 3').walk() == 6

def test_arith_shortlist_with(addlist_parser):
    "Test modifier * with things"
    assert addlist_parser.parse('shortlist 2 1 3').walk() == 6

def test_arith_shortlist_without(addlist_parser):
    "Ttest modifier * without things"
    assert addlist_parser.parse('shortlist').walk() == 0
