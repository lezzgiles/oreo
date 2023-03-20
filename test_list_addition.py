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
               (['SINGLE','NUMBER'], lambda a,b: b.value()),
               (['OPTIONAL','NUMBER?'], lambda a,b: sum([i.value() for i in b])),
               (['LONGLIST','NUMBER+'], lambda a,b: sum([i.value() for i in b])),
               (['SHORTLIST','NUMBER*'], lambda a,b: sum([i.value() for i in b])),
               ],tokenizer=t)

    return p

def test_arith_optional_with(addlist_parser):
    assert addlist_parser.parse('optional 1').value() == 1

def test_arith_optional_without(addlist_parser):
    assert addlist_parser.parse('optional ').value() == 0

def test_arith_longlist(addlist_parser):
    assert addlist_parser.parse('longlist 2 1 3').value() == 6

def test_arith_shortlist_with(addlist_parser):
    assert addlist_parser.parse('shortlist 2 1 3').value() == 6

def test_arith_shortlist_without(addlist_parser):
    assert addlist_parser.parse('shortlist').value() == 0
