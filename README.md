# oreo

Parser for Domain Specific Languages, pure python, single file module.

Features of oreo:

- Parser uses a simple BNF-inspired syntax, with modifiers ?, * and +
- The grammar also includes an optional "walk()" function for each non-terminal and terminal, so the runtime behavour of the parsed input can be defined in the same structure as the grammar.  
- The walk() functions can share one or more context variables to store state as the input is walked.
- Comment styles can be specified
- INDENT and OUTDENT tokens are supported for python-like indentation, with optional support for tab matching a set number of spaces

Features not yet implemented:
- Each parser non-terminal rule specifies a tokenizer (or inherits the tokenizer from the parent rule).  This means a single grammar can tokenize different parts of the input differently, e.g. strings can contain internal structure that is parsed.
- Error messages contain line and column
- Yaml support with INDENT happening inside a line, e.g.
this
- a: 1
  b: 2
- c: 3
  d: 4