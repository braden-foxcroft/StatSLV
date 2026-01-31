

"""
This module provides a parse(fileStr) function.
lex(fileString) can be used to get a list of tokens, if desired.
The AST class contains some of the static analysis code.
"""

from color import * # Functions for making text change color.

# For testing purposes only.
def inp():
    """Get a file from the command line. Used for testing, before the main module is built."""
    import sys
    print("Quit with ctrl-z and enter (on Windows) or ctrl-d (I think?) on linux.\nEnter file below:")
    return sys.stdin.read()
t1 = 'for i from 1 to 3\n\ti = i + 1 + 2 + 3 * i // 2\n\tif i != 32\n\t\ti = 0\ndone\nfail\npass\n'
t2 = 'for program from 1 to 3\n\ti = i + 1 + 2 + 3 * i // 2\n\tif i != 32\n\t\tbreak\ndone\nfail\npass\n'
t3 = 'if select(1 to 3) == 1\n\ti = select(select(1,3),select(4,6))'
t4 = 'j = 0\nfor i from 1 to 3\n\tj = j + i'
t5 = 'q = 0\ni = 1\nfor j from 1 to 5\n\tif i < 10\n\t\ti = i + j\nprint "abc"\n'
t6 = 'i = 1\nj = 2\nk = i + j\n'


class PosChar:
    """A character with an attached pos.
    Supports this.pos, this + other. However, this + other returns a regular str."""
    def __init__(this,char,pos,line="<No line provided>"):
        this.char = char
        this.pos = pos
        this.line = line
    def __str__(this): return this.char
    def __repr__(this): return f"PosChar({repr(this.char)},{this.pos})"
    def __add__(this,other): return str(this) + other
    def __radd__(this,other): return other + str(this)
    def __eq__(this,other): return this.char == other
    def __hash__(this): return hash(this.char)
    def charAtPos(this):
        """Returns a str of the format 'char' at pos ..."""
        if this.pos == None: return f"char {repr(this.char)} at end of file"
        return f"char {repr(this.char)} at position {this.pos[0]} on line {this.pos[1]} (offset+{this.pos[2]})"

class PosIter:
    """Takes an iterator or iterable over a string, creates an iterable over the same string with chars replaced with PosChar objects."""
    def __init__(this,fileCont):
        """Takes an iterator or iterable over a string, creates an iterable over the same string with chars replaced with PosChar objects."""
        this._iter = iter(fileCont)
        this._offset = 0
        this._line = 1
        this._char = 0
        this._lineStr = []
    
    def __iter__(this): return this
    
    def __next__(this):
        """Get next char, update the internal values"""
        res = next(this._iter)
        this._offset += 1
        while res == "\r":
            res = next(this._iter)
            this._offset += 1
        if res == "\n":
            this._line += 1
            this._char = 0
            this._lineStr = []
        else:
            this._char += 1
            this._lineStr.append(res)
        return PosChar(res,(this._char,this._line,this._offset),this._lineStr)


class Seq:
    """A class supporting peek and pop interfaces. Used for getting items from an iterable."""
    def __init__(this,iterable,terminatingVal):
        """Takes an iterable (which it converts to a list) and a value to provide once there are no more values."""
        this._ls = list(iterable)
        this._pos = 0
        this._end = terminatingVal
    
    @property
    def peek(this):
        """The next value to return."""
        if this._pos >= len(this._ls): return this._end
        return this._ls[this._pos]
    
    def pop(this):
        """Returns the next value and advances the pointer"""
        if this._pos >= len(this._ls): return this._end
        res = this._ls[this._pos]
        this._pos += 1
        return res

class Token:
    """A token class. Tracks the raw str which generated it, the value,
    whether it's a keyword and/or operator, and its type (int literal, varname, str literal)"""
    
    # A set of keyword and operator literals. An item may appear in both. Items in either will not be considered variable names.
    operators = {"+", "-", "*", "//", "to", ",", "!", "==", "!=", "<=", ">=", "<", ">", "or", "and", "not", "select", "input", "sorted", "=", "(",")","."}
    keywords = {"select", "from", "where", "for", "in", "if", "else", "elif", "bychance", "print", "nop", "input", "sorted", "{", "}", "\n","()","$","_"}
    # Determines if repr(Token(...)) should reconstruct the object or just provide a simple rep.
    # Can change Token.fullRep to change all display settings, or this.fullRep to change this one only.
    fullRep = False
    
    
    def __init__(this,raw,pos,line="No line provided",val=None):
        """raw: a raw string representing the token
        pos: a 3-item tuple (char,line,offset), or -1 (End of file), or None (unknown pos)
        val: a processed int or str for int or str literals"""
        if isinstance(raw,PosChar): raw = str(raw)
        this._isOp = raw in this.operators # operator or bracket
        this._isKeyword = raw in this.keywords # Language-defined keyword
        if isinstance(val,int): # int literal
            this._isInt = True
        else:
            this._isInt = False
        if isinstance(val,str): # String literal
            this._isStr = True
        else:
            this._isStr = False
        this._isVar = not (this._isInt or this._isStr or this._isOp or this._isKeyword or raw in ["\n","\0","{","}"]) # Variable name
        this._raw = raw
        this._pos = pos
        this._val = val
        this._line = "".join(line) # Convert a list of chars to a str.
    
    @property
    def isOp(this):
        """Operator or bracket. Operators can be keywords."""
        return this._isOp
    @property
    def isKeyword(this):
        """Keyword (used for command syntax). Keywords can be operators."""
        return this._isKeyword
    @property
    def isInt(this):
        """Integer literal. Value can be gotten with this.val"""
        return this._isInt
    @property
    def isStr(this):
        """String literal. Value can be gotten with this.val"""
        return this._isStr
    @property
    def isVar(this):
        """Variable name."""
        return this._isVar
    @property
    def raw(this):
        """The raw string which generated the token."""
        return this._raw
    @property
    def pos(this):
        """The position of the token, as a tuple. (or -1 or None)"""
        return this._pos
    @property
    def line(this):
        """The str representing the line. Available for all token types."""
        return this._line
    
    def __str__(this):
        if this._pos == -1: return f"token {repr(this.raw)} at the end of the file."
        if this._pos == None: return f"token {repr(this.raw)} at unknown position."
        return f"token {repr(this.raw)} at char {this._pos[0]} on line {this._pos[1]} (offset+{this._pos[2]})"
    def __repr__(this):
        if not this.fullRep:
            # Simple rep
            if this.isInt: return repr(this.val)
            return repr(this.raw)
        if this._val != None:
            return f"Token(raw = {repr(this.raw)}, pos = {repr(this._pos)}, line = {repr(this.line)}, val = {repr(this.val)})"
        if this._line != "No line provided":
            return f"Token(raw = {repr(this.raw)}, pos = {repr(this._pos)}, line = {repr(this.line)})"
        return f"Token(raw = {repr(this.raw)}, pos = {repr(this._pos)})"
    
    @property
    def val(this):
        """Returns the value for int or string literals. Otherwise, returns raw."""
        if this._val == None: return this._raw
        return this._val
    
    def __eq__(this,other):
        """Compares to the raw string, or the int value for integer literals."""
        if this.isInt: return this.val == other
        return this.raw == other

def error(msg):
    """Prints an error message on stderr."""
    try:
        import sys
        print(msg,file=sys.stderr)
    except: # Try again, but print to stdout instead
        print(msg)
    exit(1)


def getIndent(s,ind):
    """Takes a Seq and integer indentation depth, reads a series of '\t' chars off the iterator.
    Returns a new indentation depth and list of "{" or "}" Tokens, representing the change in indentation."""
    if s.peek == None: return 0, ([Token("}",None)] * ind)
    pos = None
    newInd = 0
    while s.peek == "\t":
        if pos == None: pos = s.peek.pos
        s.pop()
        newInd += 1
    if newInd > ind: return newInd, ([Token("{",pos)] * (newInd - ind))
    if newInd < ind: return newInd, ([Token("}",pos)] * (ind - newInd))
    return newInd,[]


def isDigit(char):
    """Checks if a char is a digit."""
    return str(char) in {"0","1","2","3","4","5","6","7","8","9"}
def isAlpha(char):
    char = str(char)
    """Checks if a char is a lowercase or uppercase letter."""
    if ord(char) >= ord("a") and ord(char) <= ord("z"): return True
    return ord(char) >= ord("A") and ord(char) <= ord("Z")


def lex(fileStr):
    """Takes a file as a str, returns a list of Token objects."""
    res = []
    pI = PosIter(fileStr) # Used to get char, line, offset of token.
    s = Seq(pI,PosChar("\0",None)) # The sequence to read from, supporting pop() and peek.
    ind = 0 # The current level of indentation.
    # Update indentation level.
    ind,toks = getIndent(s,ind)
    res += toks
    # Main loop.
    while s.peek != "\0":
        char = s.pop()
        # Advance until char isn't space.
        while char == " ": char = s.pop()
        
        # The various token possibilities
        if char in ["$",".",",",")",":"]:
            res.append(Token(char,char.pos,char.line))
        elif str(char) in {"+","-","*","!","<",">","="}:
            # All tokens which are either 't' or 't='.
            if s.peek == "=": res.append(Token(char + s.pop(), char.pos,char.line))
            else: res.append(Token(char,char.pos,char.line))
        elif char == "(":
            if s.peek == ")":
                res.append(Token(char + s.pop(),char.pos,char.line,()))
            else:
                res.append(Token(char,char.pos,char.line))
        elif char == "/":
            if s.peek == "/":
                res.append(Token(char + s.pop(),char.pos,char.line))
            elif s.peek == "*":
                s.pop()
                # Handle multi-line comments.
                while True:
                    if s.peek == "\0":
                        error("Expected '*/' at end of multi-line comment, got end of file instead.")
                    if s.peek == "*":
                        s.pop()
                        # Expect */
                        if s.peek == "/":
                            s.pop()
                            break
                    s.pop()
            else:
                res.append(Token(char,char.pos,char.line))
        elif char == "#" or char == "\n":
            if char == "#":
                # Read chars until end of line or file.
                while char != "\0" and char != "\n": char = s.pop()
            if char == "\n": # Linebreak token.
                res.append(Token(char,char.pos,char.line))
                # Handle new indentation level.
                ind,toks = getIndent(s,ind)
                res += toks
        elif isDigit(char):
            # int literal
            num = "" + char # To ensure str.
            while isDigit(s.peek): num += s.pop()
            res.append(Token(num,char.pos,char.line,int(num)))
            if s.peek == ".":
                error(f"{red('This language does not support floating point numbers.')}\nConsider using fractions instead (for example {col_int(2)} / {col_int(3)}). The 'A . B' notation is a binary operator meaning \"convert A to a float, then round to B decimal places. Finally, convert the result to a string.\"\nTo prevent this warning, put a space between the int literal and dot.\n{red('Error occured when parsing')} {col_str(s.peek.charAtPos())}")
        elif char == "\"":
            # str literal
            raw = "\""
            val = ""
            escapes = {"n":"\n","r":"\r","t":"\t","\\":"\\","\"":"\""}
            while s.peek != "\"":
                if s.peek == "\n" or s.peek == "\r":
                    error(f"Unexpected char inside string literal: {s.peek.charAtPos()}")
                if s.peek == "\0":
                    error("Expected '\"' at end of string literal, got end of file instead.")
                if s.peek == "\\": # Escape sequence
                    raw += s.pop()
                    if str(s.peek) not in escapes:
                        error(f"Unknown escaped char inside string literal: {s.peek.charAtPos()}")
                    raw += s.peek
                    val += escapes[s.pop()]
                    continue
                raw += s.peek
                val += s.pop()
            raw += s.pop() # Ending quotation mark
            res.append(Token(raw,char.pos,char.line,val))
        elif isAlpha(char) or char == "~":
            # var name or keyword
            name = str(char)
            while isAlpha(s.peek) or isDigit(s.peek) or s.peek == "_" or s.peek == "~": name += s.pop()
            res.append(Token(name,char.pos,char.line))
        elif char == "_":
            res.append(Token(char,char.pos,char.line))
        else:
            error(f"Unexpected char at start of token: {char.charAtPos()}")
    res.append(Token("\n",-1,"<Compiler added linebreak at end of file>")) # To always end on an empty line.
    ind,toks = getIndent(s,ind)
    res += toks
    return res

# TODO test lexer

class AST:
    """An Abstract Syntax Tree node. Every child must also be an AST node, even int literals.
    Behaves like a value for the purposes of equality, and like a list for indexing or iterating."""
    def __init__(this,val,children,nodeType):
        """Takes the value at the node (a token), and a list of however many AST children the the node requires.
        'nodeType' should be string, like program, block, command, expr, opB, opU, var, int, str"""
        if not isinstance(val,Token): raise Exception(f"AST val must be of type Token! (Got type {type(val)} instead of {Token})")
        if not isinstance(children,list): raise Exception(f"AST children must be of type 'list'! (Got type {type(children)} instead)")
        for child in children:
            if not isinstance(child,AST): raise Exception(f"AST children must be AST nodes as well! (Got type {type(child)} instead)")
        if not isinstance(nodeType,str): raise Exception(f"AST nodeType must be of type 'str'! (Got type {type(nodeType)} instead)")
        this._val = val
        this._children = list(children)
        validTypes = ["program","block","command","expr","opB","opU","var","int","str","list"]
        if nodeType not in validTypes:
            raise Exception(f"Expected node of one of these types: {validTypes}\nGot node of type {repr(nodeType)}")
        this._type = nodeType
        this.discards = {}
    
    def __eq__(this,other):
        """Checks if this is the same as the other."""
        return this is other
    def __hash__(this):
        """The object ID"""
        return id(this)
    
    def __iter__(this): return iter(this._children)
    
    def __getitem__(this,index): return this._children[index]
    
    def __len__(this): return len(this._children)
    
    @property
    def val(this):
        """The token at the root of the current subtree"""
        return this._val
    @property
    def pos(this):
        """Returns the position of the val"""
        return this.val.pos
    @property
    def nodeType(this):
        """Returns the type of the node."""
        return this._type
    def opB(this):
        """Checks if the AST node is an operator taking two inputs (binary operator)"""
        return this.val in ["*", "//", "%", "/", ".", "+", "-", "to", ",", "==", "!=", "<=" ">=", "<", ">", "and", "or"]
    def opU(this):
        """Checks if the AST node is an operator taking a single input."""
        return this.val in ["select","not"]
        
    
    def __str__(this): return this._build(0)
    def __repr__(this): return f"AST({repr(this._val)},{repr(this._children)},{repr(this._type)})"
    
    def _build(this,indent):
        res = "\t" * indent + this.val.raw
        for child in this:
            res += "\n" + child._build(indent+1)
        return res
    
    def filter(this,function = lambda node : True):
        """Returns a list of AST nodes for which function(node) returns True."""
        res = []
        if function(this):
            res.append(this)
        for child in this:
            res += child.filter(function)
        return res
    
    def forAll(this,function = lambda node : None):
        """Applies a mutation function upon every node. Applies to the root first."""
        function(this)
        for child in this:
            child.forAll(function)
        return
    
    def modify(this,function = lambda node: [node]):
        """Modifies the AST by applying 'function' to each command node, and replacing the command in the list with
        the list of commands produced by 'function'. 'function' takes a node and returns a list of nodes.
        This is not a mutation operation; it makes a new AST.
        The 'function' applies to the child nodes before the parent.
        """
        res = []
        for child in this:
            res += child.modify(function)
        new = AST(this.val,res,this.nodeType)
        if new.nodeType == "command":
            return function(new)
        if new.nodeType == "program":
            return new
        return [new]
        
    def comment(this,cont):
        if cont == "" or cont == None or cont == "None":
            return ""
        return col_comment(" # " + str(cont))
    
    def reconstruct(this,indent=0,funcArg=None):
        """Reconstructs the AST as a string. 'color' determines if to add syntax highlighting. 'indent' determines the working level of indentation."""
        if funcArg == None:
            func = lambda command : ""
        else:
            func = funcArg
        res = ""
        keyword = col_keyword
        if this.nodeType == "program":
            for child in this:
                res += child.reconstruct(indent,funcArg)
            return res + "\n"
        if this.nodeType == "block":
            if len(this) == 0:
                return "\t"*(indent+1) + keyword("nop") + "\n"
            for child in this:
                res += child.reconstruct(indent+1,funcArg)
            return res
        if this.nodeType == "command" and this.val == "for":
            res += "\t"*indent+keyword("for ")+this[0].reconstruct(indent,funcArg)+keyword(" from ")+this[1].reconstruct(indent,funcArg)+this.comment(func(this))+"\n"
            res += this[2].reconstruct(indent,funcArg)
            return res
        if this.nodeType == "command" and this.val == "if":
            res += "\t"*indent+keyword("if ")+this[0].reconstruct(indent,funcArg)+this.comment(func(this))+"\n"
            res += this[1].reconstruct(indent,funcArg)
            # Create an iterator which skips the first 2 elements
            i = iter(this)
            next(i)
            next(i)
            # Iterate over the remaining children
            for condition in i:
                block = next(i) # If this fails, the AST node is poorly formatted. The children are consecutive expr, block pairs.
                res += "\t"*indent+keyword("elif ")+condition.reconstruct(indent,funcArg)+"\n"
                res += block.reconstruct(indent,funcArg)
            return res
        if this.nodeType == "command" and this.val == "set":
            return "\t"*indent+this[0].reconstruct(indent,funcArg)+" "+this[1].reconstruct(indent,funcArg)+" "+this[2].reconstruct(indent,funcArg)+this.comment(func(this))+"\n"
        if this.nodeType == "command" and this.val == "select":
            return "\t"*indent+keyword("select ")+this[0].reconstruct(indent,funcArg)+keyword(" from ")+this[1].reconstruct(indent,funcArg)+keyword(" where ")+this[2].reconstruct(indent,funcArg)+this.comment(func(this))+"\n"
        if this.nodeType == "command" and this.val == "input":
            return "\t"*indent + keyword("input ") + this[0].reconstruct(indent,funcArg) + " " + this[1].reconstruct(indent,funcArg) + this.comment(func(this))+"\n"
        if this.nodeType == "command" and this.val == "nop":
            return "\t"*indent + keyword("nop") + this.comment(func(this)) + "\n"
        if this.nodeType == "var":
            return this.val.raw
        if this.nodeType == "command" and this.val in ["pass","fail","done"]:
            return "\t"*indent+keyword(this.val.raw)+this.comment(func(this))+"\n"
        if this.nodeType == "command" and this.val in ["return","print","bychance"]:
            return "\t"*indent+keyword(this.val.raw) + " " + this[0].reconstruct(indent,funcArg) + this.comment(func(this)) + "\n"
        if this.nodeType == "str":
            return col_str(this.val.raw)
        if this.nodeType == "int":
            return col_int(this.val.raw)
        if len(this) == 0: # Literal or var name.
            return this.val.raw
        if this.nodeType == "expr":
            return this[0].reconstruct(indent,funcArg)
        if this.nodeType == "opB":
            if this.val.raw in ["in","not","or","and","to"]:
                return f"({this[0].reconstruct(indent,funcArg)} {keyword(this.val.raw)} {this[1].reconstruct(indent,funcArg)})"
            else:
                return f"({this[0].reconstruct(indent,funcArg)} {this.val.raw} {this[1].reconstruct(indent,funcArg)})"
        if this.nodeType == "opU":
            return f"{this.val.raw}({this[0].reconstruct(indent,funcArg)})"
        raise Exception(f"Unhandled case: could not reconstruct string form of AST node with root: {this.val}")



# TODO test parser

def parse(fileStr):
    """Takes a file string, returns a block of code as an AST"""
    tokens = lex(fileStr)
    s = Seq(tokens,Token("\0",-1))
    return parseProg(s)


def parseBlock(s):
    """If no seq is provided, returns an empty block AST (for convenience)"""
    if s == None: return AST(Token("block",None),[],"block")
    pos = expect(s,"{").pos
    res = []
    while s.peek != "}":
        com = parseCommand(s)
        if com != None:
            res.append(com)
    s.pop()
    return AST(Token("block",pos),res,"block")

def parseProg(s):
    res = []
    while s.peek != "\0":
        com = parseCommand(s)
        if com != None:
            res.append(com)
    if len(res) == 0 or res[-1].val != "done":
        res.append(AST(Token("done",-1,"Program done"),[],"command"))
    return AST(Token("program",(0,0,0)),res,"program")


def parseCommand(s):
    res = []
    if s.peek == "\n":
        s.pop()
        return None
    if s.peek == "select":
        com = s.pop()
        var = parseVar(s)
        expect(s,"from")
        expr = parseExpr(s)
        if s.peek == "where":
            s.pop()
            expr2 = parseExpr(s)
        else:
            expr2 = AST(Token("1",com.pos,com.line,1),[],"int") # The expression 'True'
        expect(s,"\n")
        return AST(com,[var,expr,expr2],"command")
    if s.peek in ["pass","fail","done","nop"]:
        com = s.pop()
        expect(s,"\n")
        return AST(com,[],"command")
    if s.peek in ["return","bychance","print"]:
        com = s.pop()
        # Take a single expr argument
        expr = parseExpr(s)
        expect(s,"\n")
        return AST(com,[expr],"command")
    if s.peek == "input":
        com = s.pop()
        var = parseVar(s)
        expr = parseExpr(s)
        return AST(com,[var,expr],"command")
    if s.peek == "for":
        com = s.pop()
        var = parseVar(s)
        if s.peek not in ["in","from"]:
            error(f"Expected 'in' or 'from', got {s.peek}")
        s.pop()
        expr = parseExpr(s)
        optional(s,":")
        expect(s,"\n")
        block = parseBlock(s)
        return AST(com,[var,expr,block],"command")
    if s.peek == "if":
        com = s.pop()
        # Result is a series of ASTs: expr, block, expr, block...
        # 'else' is just 'elif 1'
        res = []
        expr = parseExpr(s)
        optional(s,":")
        expect(s,"\n")
        block = parseBlock(s)
        res += [expr,block]
        while s.peek == "elif" or s.peek == "else":
            if s.peek == "else":
                expr = AST(Token("1",s.peek.pos,s.pop().line,1),[],"int") # The expression 'True'
                optional(":")
                expect(s,"\n")
                block = parseBlock(s)
            else: # s.peek == "elif"
                s.pop()
                expr = parseExpr(s)
                optional(s,":")
                expect(s,"\n")
                block = parseBlock(s)
            res += [expr,block]
        return AST(com,res,"command")
    # Default case is var assignOp expr
    var = parseVar(s)
    op = getAssignOp(s)
    expr = parseExpr(s)
    return AST(Token("set",var.pos,var.val.line),[var,AST(op,[],"opB"),expr],"command")


def optional(s,expected):
    """Removes the expected token if present"""
    if s.peek == expected:
        s.pop()

def expect(s,expected):
    """Expects the next token to be 'expected', and exits otherwise. Returns the expected token."""
    if s.peek != expected:
        error(f"Expected {repr(expected)}, got {s.peek}")
    return s.pop()

def parseVar(s):
    """Returns a var node"""
    if s.peek.isKeyword and (s.peek in ["$","_"]):
        return AST(s.pop(),[],"var")
    if not s.peek.isVar:
        error(f"Expected varname, got {s.peek}")
    return AST(s.pop(),[],"var")

def getAssignOp(s):
    """Expects and returns an assignment operator token."""
    if s.peek not in ["="]:
        error(f"Expected assignment operator (=), got {s.peek}")
    return s.pop()


def parseExpr(s):
    """Parses an expression from the stack. Returns an node of type expr."""
    pos = s.peek.pos
    expr = parseExpr1(s)
    return AST(Token("expr",pos),[expr],"expr")
    


def parseExpr1(s):
    """expr1 = expr2 {or expr2}"""
    expr = parseExpr2(s)
    while s.peek == "or":
        op = s.pop()
        expr2 = parseExpr2(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr
    

def parseExpr2(s):
    """expr2 = expr3 {and expr3}"""
    expr = parseExpr3(s)
    while s.peek == "and":
        op = s.pop()
        expr2 = parseExpr3(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr
    

def parseExpr3(s):
    """expr3 = expr4 {("==" | "!=" | "<=" | ">=" | "<=" | ">" | "<") expr4}"""
    expr = parseExpr3B(s)
    while s.peek in ["==","!=","<=",">=",">","<"]:
        op = s.pop()
        expr2 = parseExpr3B(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr

def parseExpr3B(s):
    """expr4B = expr5 {"in" expr5}"""
    expr = parseExpr4(s)
    while s.peek == "in":
        op = s.pop()
        expr2 = parseExpr4(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr

def parseExpr4(s):
    """expr4 = expr4B {"," [expr4B]}"""
    expr = parseExpr5(s)
    while s.peek == ",":
        op = s.pop()
        if s.peek == ")":
            expr2 = AST(Token("("+s.peek.raw,s.peek.pos,s.peek.line,()),[],"list")
        else:
            expr2 = parseExpr5(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr

def parseExpr5(s):
    """expr5 = expr6 {"to" expr6}"""
    expr = parseExpr6(s)
    while s.peek in ["to"]:
        op = s.pop()
        expr2 = parseExpr6(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr

def parseExpr6(s):
    """expr6 = expr7 {("+" | "-") expr7}"""
    expr = parseExpr7(s)
    while s.peek in ["+","-"]:
        op = s.pop()
        expr2 = parseExpr7(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr

def parseExpr7(s):
    """expr7 = expr8 {("*" | "//" | "%" | "/") expr8}"""
    expr = parseExpr8(s)
    while s.peek in ["*","//","%","/","."]:
        op = s.pop()
        expr2 = parseExpr8(s)
        expr = AST(op,[expr,expr2],"opB")
    return expr

def parseExpr8(s):
    """expr8 = ["!" | "-" | "select" | "not" | "input" | "sorted"] expr9"""
    if s.peek in ["!","-","select","not","input","sorted"]:
        op = s.pop()
        if op == "!": # '!' is just 'not'
            op.raw = "not"
        expr = parseExpr9(s)
        return AST(op,[expr],"opU")
    expr = parseExpr9(s)
    return expr
    

def parseExpr9(s):
    """expr9 = int | var | "$"" | "_" | string | "(" expr1 ")" """
    if s.peek.isVar:
        return AST(s.pop(),[],"var")
    if s.peek.isInt:
        return AST(s.pop(),[],"int")
    if s.peek.isStr:
        return AST(s.pop(),[],"str")
    if s.peek.isKeyword and (s.peek in ["$","_"]):
        return AST(s.pop(),[],"var")
    if s.peek == "()":
        return AST(s.pop(),[],"list")
    if s.peek != "(":
        error(f"While parsing an expression, expected a value, '(', or a unary operator. Got: {s.peek}")
    s.pop()
    expr = parseExpr1(s)
    expect(s,")")
    return expr







