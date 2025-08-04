
# TODO update comment once done.
"""
The major methods from this module are lex(fileString) and, in future, parse(tokens)
"""



class PosChar:
    """A character with an attached pos.
    Supports this.pos, this + other. However, this + other returns a regular str."""
    def __init__(this,char,pos):
        this.char = char
        this.pos = pos
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
        else:
            this._char += 1
        return PosChar(res,(this._char,this._line,this._offset))


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
    
    # A set of keyword and operator literals.
    operators = {"+", "-", "*", "//", "to", ",", "!", "==", "!=", "<=", ">=", "<", ">", "or", "and", "not", "select", "=", "+=", "-=", "*=","(",")"}
    keywords = {"select", "from", "where", "for", "in", "if", "else", "elif", "break", "continue", "bychance", "print", "{", "}", "\n"}
    # Determines if repr(Token(...)) should reconstruct the object or just provide a simple rep.
    # Can change Token.fullRep to change all display settings, or this.fullRep to change this one only.
    fullRep = False
    
    
    def __init__(this,raw,pos,val=None):
        """raw: a raw string representing the token
        pos: a 3-item tuple (char,line,offset) or None
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
        this._isVar = not (this._isInt or this._isStr or this._isOp or this._isKeyword) # Variable name
        this._raw = raw
        this._pos = pos
        this._val = val
    
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
    
    def __str__(this):
        if this._pos == None: return f"token {repr(this.raw)} at the end of the file."
        return f"token {repr(this.raw)} at char {this._pos[0]} on line {this._pos[1]} (offset+{this._pos[2]})"
    def __repr__(this):
        if not this.fullRep:
            # Simple rep
            if this.isInt: return repr(this.val)
            return repr(this.raw)
        if this._val == None: return f"Token(raw = {repr(this.raw)}, pos = {repr(this._pos)})"
        return f"Token(raw = {repr(this.raw)}, pos = {repr(this._pos)}, val = {repr(this.val)})"
    
    @property
    def val(this):
        """Returns the value for int or string literals. Otherwise, throws an error."""
        if this._val == None: raise Exception("Tried to get Token.val for a token which wasn't a str or int literal.")
        return this._val
    
    def __eq__(this,other):
        """Converts to the token type. (int for int literal, str for string literal, raw str for everything else.)"""
        if this.isInt or this.isStr: return this.val == other
        return this.raw == other

def error(msg):
    """Prints an error message on stderr."""
    try:
        import sys
        print(msg,file=sys.stderr)
    except:
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
        if char == "(":
            res.append(Token("(",char.pos))
        elif char == ")":
            res.append(Token(")",char.pos))
        elif str(char) in {"+","-","*","!","<",">","="}:
            # All tokens which are either 't' or 't='.
            if s.peek == "=": res.append(Token(char + s.pop(), char.pos))
            else: res.append(Token(char,char.pos))
        elif char == "/":
            if s.peek == "/":
                res.append(Token(char + s.pop(),char.pos))
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
                error(f"expected '/*' or '//', got '/' followed by {s.peek.charAtPos()}")
        elif char == "#" or char == "\n":
            if char == "#":
                # Read chars until end of line or file.
                while s.peek != "\0" and s.peek != "\n": s.pop()
            if s.peek == "\n": # Linebreak token.
                res.append(Token(s.pop(),char.pos))
        elif isDigit(char):
            # int literal
            pos = char.pos
            num = "" + char # To ensure str.
            while isDigit(s.peek): num += s.pop()
            res.append(Token(num,pos,int(num)))
        elif char == "\"":
            # str literal
            pos = char.pos
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
            res.append(Token(raw,pos,val))
        elif isAlpha(char):
            # var name or keyword
            name = str(char)
            pos = char.pos
            while isAlpha(s.peek) or isDigit(s.peek) or s.peek == "_": name += s.pop()
            res.append(Token(name,pos))
        elif char == "_":
            res.append(Token(char,char.pos))
        else:
            error(f"Unexpected char: {char.charAtPos()}")
    return res
    
    


# TODO test lexer

# TODO parser

