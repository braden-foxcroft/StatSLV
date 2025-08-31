# StatSLV
This is a programming language developed by Braden Foxcroft (me) in order to create a convenient solver for statistics word problems.
The language is interpreted, and the interpreter is written entirely in `Python 3.13`, using only the standard library. It can be ran using:

> python main.py filename.txt

The interpreter also supports several command-line flags, such as '-p' and '-P'. For a full list, type `python main.py -h`. (Many features are not supported yet, however, so keep this in mind. This project is under development and will likely remain that way for several months.)
# To run

> python main.py examples\twoDice.txt

If you don't have python, you'll have to install it first. The command should be run from the command line, in the same folder as this readme.

# What next?
- A better readme file
- Automatic variable discards (when a variable is no longer used, its value should be discarded automatically, causing branches to unify earlier)
- A fair bit of testing (sooo much testing)
- A text debugger, so you can see what your code is doing
- Maybe even a GUI debugger? That would probably be more work than its worth, though.
- Better `print` statements, so you can see what your code is doing. I'm not convinced this is particularly feasible, though. Especially when you combine `print` statements and `for` loops where different paths loop over different ranges, the code execution order becomes somewhat hard to make sense of.
- User input? How would input even work in a multi-path execution?
- Better documentation and further examples
- Cleaning up of the syntax and semantics.
- Better error messages
- More command-line options
- Arrays: [], [val, val, ...], 'in' and 'not in' operators. Array[index] operator.
- Do I want dictionaries? They aren't hashable, though, so they can't easily be unified with other paths.
- A proper explanation for how the interpreter does its magic.