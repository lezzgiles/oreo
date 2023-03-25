# oreo

Parser for Domain Specific Languages, pure python, single file module.

Features of oreo:

- Parser uses a simple BNF-inspired syntax, with modifiers ?, * and +
- The grammar also includes an optional "walk()" function for each non-terminal and terminal, so the runtime behavour of the parsed input can be defined in the same structure as the grammar.  
- The walk() functions can share one or more context variables to store state as the input is walked.
- Comment styles can be specified
- INDENT and OUTDENT tokens are supported for python-like indentation, with optional support for tab matching a set number of spaces.
- Optionally an INDENT can start in the middle of a line, as in YAML lists
- Each parser non-terminal rule optionally specifies a tokenizer (or inherits the tokenizer from the parent rule).  This means a single grammar can tokenize different parts of the input differently, e.g. strings can contain internal structure that is parsed.

## Introductory tutorial

Oreo takes a grammar that defines a formal language, and then uses that grammar to parse a "program" written in that language.  It can then optionally run the parsed program.

For a very simple case, let's start with a language that allows us to add or subtract two numbers.  Valid programs in this language would include:
> 1 + 1

> 3 - 2

We will start with a **tokenizer** which will recognize all the text elements in our language:
```
from oreo import Tokenizer,Parser
t = Tokenizer()
t.add_token('NUMBER','-?[0-9]+',lambda a: int(a))
t.add_token('PLUS','\+')
t.add_token('MINUS,'-')
```

Each token, or **terminal**, has a name and regex, and an optional walk() function.  The regex is used to find text that matches the token, and the walk() function lets us define what will happen when we "run" the code - in this case it defines the value of a NUMBER as its matching text converted to an integer.  The default walk() function simply returns the string that matches the regex.

Next we want to define the rules for valid programs:
```
parser = Parser()
parser.add_rule('start',[
    (['NUMBER','PLUS','NUMBER'],lambda a,b,c: a.walk() + c.walk()),
    (['NUMBER','MINUS','NUMBER'],lambda a,b,c: a.walk() - c.walk()),
], tokenizer=t)
```
Every grammar needs a **start** rule, and this grammar has two possible programs: one that adds two numbers, and one that subtracts two numbers.  Note that the walk() functions take the NUMBER values and add/subtract them.  The last argument to the add_parse() method is the tokenizer that will be used.

To parse a program:
```
tree = parser.parse('1 + 1')
```
This returns a **parse tree** of `Node` and `Token` objects which your python program can then inspect and manipulate as you wish.  A `Node` object has fields `rule` and `children`, set to the name of the rule and the Nodes or Tokens for all elements of the rule that matched, and a `Token` object has `token` and `body` fields, set to the name and the value of the token.  Note that this value is the actual characters that match the regex, not the value of the walk() function.

Since we defined our walk() functions, we can use them to calculate the final value of our program:
```
value = tree.walk()
```
Or we can simplify:
```
value = parser.parse('1 + 1').walk()
```

## Tokenizer

### Tokenizer()
The tokenizer constructor takes one option that change how the tokenizer works:
#### ignore_whitespace=True
Most of the time you'll want your tokenizer to simply skip over and ignore whitespace.  If this flag is True then `1 + 1` is the same as `1+1` or `1+     1`.  Set this flag to False if you want space or tab characters to have a special meaning.
### tokenizer.add_comment_style(regex,flags=0)
This method takes a regex that match comments and an optional flag setting.  A couple of useful comment styles:
```
import re
t.add_comment_style('/\*.*?\*/',re.DOTALL)   # C-style comment
t.add_comment_style('#.*$',re.MULTILINE)     # Shell-style comment
```
#### tokenizer.use_indent_tokens(indent_token,outdent_token,tabsize=0,inline_indents=False)
Indent is a pseudo-token returned when the indent level of your program increases, and outdent is a pseudo-token returned when the indent level returns to an earlier level.  Since you are a python programmer, you should be familiar with these concepts.
**indent_token** and **outdent_token** are the names of the tokens you want to use in your grammar for indent and outdent; **tabsize** is the optional nominal size of a tab character - currently if this is not set then a tab character will count the same as a space for indent/outdent purposes (in the future this will change to an error condition to match what yaml and python do); **inline_indents** enables a feature that allows parsing of yaml-like languages, for example this code sample:
```
- alpha: 1
  beta: 2
```
could be tokenized to DASH, INDENT, SYMBOL, COLON, INDENT, NUMBER, OUTDENT, SYMBOL, COLON, INDENT, NUMBER, OUTDENT, OUTDENT.
### tokenizer.add_token(name,regex,walk=None)
add_token() takes the name of a symbol, by convention UPPERCASE, a regex that defines the symbol, and an optional walk() function used at runtime.  The walk() function is passed in an optional context argument or arguments followed by the text value of the token.  If the top-level Parser.walk() method is called with arguments then those same arguments are passed down to all user-defined walk() functions.  See Parser.walk() for more details on context.

## Parser
A grammar must have a 'start' rule, created using the add_rule() method.
### parser.add_rule(name,body,tokenizer=None)
This method adds a named rule to the grammar.

The **name** of the rule is a symbol, by convention lowercase.
The **body** is a list of pairs, of pattern and walk() function.  The pattern is a list of tokens and rules, where each item can be followed by one of \*, +, or ?, where these characters have their normal regex meanings.  For example:
```
[ 'START', 'statement+', 'END' ]
```
The corresponding walk() function takes arguments for each item in the pattern; for items with modifier \*, \+ or \?, the argument passed to the walk() function is a list; for items without modifiers, the argument passed to the walk() function is the value of the walk() function called for that parsed element.
The optional **tokenizer** is the Tokenizer object used to tokenize the input for this rule.  If no tokenizer is specified, then the tokenizer used in the parent rule is used.  A tokenizer must be specified for the **start** rule.
### parser.parse(input,trace=False)
Parses the text in input into a parsetree.  The root of the parsetree is a **Node**.  The optional **trace** flag will turn on tracing during the parse, to help with troubleshooting.
## Node
### node.walk(context,...)
The walk() method will normally be called on the parsetree returned by parser.parse().  Any arguments passed in to node.walk() are passed on to all recursive calls to walk() methods, and this mechanism is provided to enable a runtime context that can be manipulated by the various walk() methods.  For example, if context is set to a dictionary, then this could be the body of a rule that assigns a value to a runtime variable:
```
( [ 'VARIABLE', 'EQUALS', 'NUMBER' ], lambda ctx,a,b,c: ctx[a.value(ctx)] = c.value(ctx) )
```
And this might be the parser rule to get a value:
```
p.add_rule('number-term',[
    (['NUMBER'], lambda ctx,a: a.walk(ctx)),
    (['SYMBOL'], lambda ctx,a: ctx[a.value(ctx)]),
])
```
Note that the walk() functions defined in the rule must explicitly pass down any context variables.
## To do
- Add location details to Node and Token objects
- tabsize = 0 should cause an error if a tab is found in whitespace
