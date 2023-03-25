from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException

import pytest

@pytest.fixture
def simple_parser():
    body_tokenizer = Tokenizer()
    body_tokenizer.add_token('LET','let')
    body_tokenizer.add_token('SYMBOL','[a-zA-Z]+')
    body_tokenizer.add_token('EQUALS','=')
    body_tokenizer.add_token('QUOTE','"')

    string_tokenizer = Tokenizer()
    string_tokenizer.add_token('HEX','[0-9A-F][0-9A-F]',lambda a: chr(int(a,16)))
    

    p = Parser()
    p.add_rule('start',[(['LET','SYMBOL','EQUALS','QUOTE','string_body','QUOTE'],lambda a,b,c,d,e,f: e.walk())],body_tokenizer)
    p.add_rule('string_body',[(['HEX+'],lambda a: ''.join([i.walk() for i in a]))],string_tokenizer)

    return p

def test_simple_indent(simple_parser):
    p = 'let a = "48 65 6C 6C 6F 20 57 6F 72 6C 64"'
    assert simple_parser.parse(p).walk() == "Hello World"
