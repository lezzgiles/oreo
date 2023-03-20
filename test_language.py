from oreo import Tokenizer,Parser,ParseFailException,ParseDefinitionException

import pytest

@pytest.fixture
def language_parser():
    t = Tokenizer()
    t.add_token('NUMBER','-?[0-9]+',lambda n: int(n))
    t.add_token('PLUS','\+')
    t.add_token('MINUS','-')
    t.add_token('MULTIPLY','\*')
    t.add_token('DIVIDE','/')
    t.add_token('OPEN_PAREN','\(')
    t.add_token('CLOSE_PAREN','\)')
    t.add_token('EQUALS','=')
    t.add_token('PRINT','print')
    t.add_token('SYMBOL','[a-zA-Z]+')
    t.add_token('SEMICOLON',';')

    p = Parser()
    p.add_rule('start',[(['statement+'],lambda a: a.value())],tokenizer=t)
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
        (['SYMBOL'], lambda a: a.value()),
    ])
    p.add_rule('statement',[
        (['PRINT','add-term','SEMICOLON'], lambda a,b,c: b.value()),
        (['SYMBOL','EQUALS','add-term','SEMICOLON'], lambda a,b,c: b.value()),
    ])
