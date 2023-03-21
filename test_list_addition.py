from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException

import pytest

@pytest.fixture
def addlist_parser():
    t = Tokenizer()
    t.add_token('NUMBER','-?[0-9]+',lambda n: int(n))
    t.add_token('SINGLE','single')
    t.add_token('OPTIONAL','optional')
    t.add_token('LONGLIST','longlist')
    t.add_token('SHORTLIST','shortlist')

    p = Parser()
    p.add_rule('start',[
               (['SINGLE','NUMBER'], lambda a,b: b.walk()),
               (['OPTIONAL','NUMBER?'], lambda a,b: sum([i.walk() for i in b])),
               (['LONGLIST','NUMBER+'], lambda a,b: sum([i.walk() for i in b])),
               (['SHORTLIST','NUMBER*'], lambda a,b: sum([i.walk() for i in b])),
               ],tokenizer=t)

    return p

def test_arith_optional_with(addlist_parser):
    assert addlist_parser.parse('optional 1').walk() == 1

def test_arith_optional_without(addlist_parser):
    assert addlist_parser.parse('optional ').walk() == 0

def test_arith_longlist(addlist_parser):
    assert addlist_parser.parse('longlist 2 1 3').walk() == 6

def test_arith_shortlist_with(addlist_parser):
    assert addlist_parser.parse('shortlist 2 1 3').walk() == 6

def test_arith_shortlist_without(addlist_parser):
    assert addlist_parser.parse('shortlist').walk() == 0
