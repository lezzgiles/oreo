"""
Test switching tokenizer inside a grammar
"""
import pytest
from oreo import Tokenizer,Parser


@pytest.fixture(name="simple_parser")
def fixture_simple_parser():
    "Grammar with two tokenizers"
    body_tokenizer = Tokenizer()
    body_tokenizer.add_token('LET','let')
    body_tokenizer.add_token('SYMBOL','[a-zA-Z]+')
    body_tokenizer.add_token('EQUALS','=')
    body_tokenizer.add_token('QUOTE','"')

    string_tokenizer = Tokenizer()
    string_tokenizer.add_token('HEX','[0-9A-F][0-9A-F]',lambda a: chr(int(a,16)))


    par = Parser()
    par.add_rule('start',[(['LET','SYMBOL','EQUALS','QUOTE','string_body','QUOTE'],lambda a,b,c,d,e,f: e.walk())],body_tokenizer)
    par.add_rule('string_body',[(['HEX+'],lambda a: ''.join([i.walk() for i in a]))],string_tokenizer)

    return par

def test_simple_indent(simple_parser):
    "Test switching tokenizer"
    prog = 'let a = "48 65 6C 6C 6F 20 57 6F 72 6C 64"'
    assert simple_parser.parse(prog).walk() == "Hello World"
