

# TODO: rewrite the code using 'peek' and 'pop' interface.
# The None value should be '\0', to prevent typing conflicts from becoming an issue.

class PosChar:
    """A character with an attached pos.
    Supports this.pos, this + other. However, this + other returns a regular str."""
    def __init__(this,string,pos):
        this.string = string
        this.pos = pos
    def __str__(this): return this.string
    def __repr__(this): return f"PosChar({repr(this.string)},{this.pos})"
    def __add__(this,other): return str(this) + other
    def __radd__(this,other): return other + str(this)
    def __eq__(this,other): return this.string == other
    # TODO nice char representation, for 'error' messages. Revise existing messages.
    def charAtPos(this):
        """Returns a str of the format 'char' at pos ..."""

class PosIter:
    """An iterator over a string which tracks the character and line position, as well as character offset.
    Skips carriage returns (\r), though uses them to calculate offset.
    Each entry is a PosChar with the required position attached."""
    def __init__(this,fileCont):
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



class PBIter:
    """An iterator with pushback (items can be put back without being used)."""
    def __init__(this,iterable):
        this._iter = iter(iterable)
        this._putBack = []
    
    def __iter__(this): return this
    
    def __next__(this):
        if this._putBack: return this._putBack.pop()
        return next(this._iter)
    
    def put(this,toPush):
        """puts the char back into the iterator. put(None) does nothing."""
        if toPush != None: this._putBack.append(toPush)
    
    def __eq__(this,nxt):
        """Checks if the next entry is equal to nxt. Returns a boolean.
        If no value is available, uses 'None'"""
        if this._putBack:
            nxt2 = this._putBack[-1]
        else:
            try:
                nxt2 = next(this._iter)
                this.put(nxt2)
            except StopIteration:
                nxt2 = None
        return nxt == nxt2
    
    def get(this):
        """Returns the next value, or None if not available.
        Mostly used for error messages after '==' fails."""
        try:
            return this.__next__()
        except StopIteration:
            return None


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
        print("(Error while printing error message on stderr; used stdout instead)") # TODO remove
        print(msg)
    exit(1)


# TODO tokenize (with token positions). Turn indent+ and indent- into tokens.

def getIndent(itr,ind):
    """Takes a PBIter and integer indentation depth, reads a series of '\t' chars off the iterator.
    Returns a new indentation depth and list of "{" or "}" Tokens, representing the change in indentation."""
    if itr == None: return 0, ([Token("}",None)] * ind)
    pos = None
    newInd = 0
    while itr == "\t":
        if pos == None: pos = itr.get().pos
        else: itr.get()
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
    itr = PBIter(pI) # The iter to read from, with pushback and lookahead capabilities.
    ind = 0 # The current level of indentation.
    # Update indentation level.
    ind,toks = getIndent(itr,ind)
    res += toks
    # Main loop.
    for char in itr:
        # If the char is space, then advance until it isn't space.
        if char == " ":
            for char in itr:
                if char != " ": break
            else: break # Ran out of chars, no more tokens.
        # 'char' is now not space.
        if char == "(":
            res.append(Token("(",char.pos))
        elif char == ")":
            res.append(Token(")",char.pos))
        elif str(char) in {"+","-","*","!","<",">","="}:
            # All tokens which are either 't' or 't='.
            if itr == "=": res.append(Token(char + itr.get(), char.pos))
            else: res.append(Token(char,char.pos))
        elif char == "/":
            if itr == "/":
                itr.get()
                res.append(Token("//",char.pos))
            elif itr == "*":
                itr.get()
                # Handle multi-line comments.
                # TODO
            else:
                error(f"expected '/*' or '//', got partial {Token(char,char.pos)}")
        elif char == "#" or char == "\n":
            if char == "#":
                # Read chars until end of line or file.
                for char in itr:
                    if char == "\n": break
                else:
                    char = None # End of file
            if char == "\n": # Linebreak token.
                res.append(Token("\n",char.pos))
        elif isDigit(char):
            # int literal
            pos = char.pos
            num = "" + char # To ensure str.
            for char in itr:
                if not isDigit(char):
                    itr.put(char)
                    break
                num += char
            res.append(Token(num,pos,int(num)))
        elif char == "\"":
            # str literal
            for char in itr:
                if char == "\n" or char == "\r":
                    error("Expected ")
            else:
                error("Expected '\"' at end of string literal, got end of file instead.")
            # TODO
            
        elif isAlpha(char):
            # var name or keyword
            name = str(char)
            pos = char.pos
            for char in itr:
                if not (isAlpha(char) or isDigit(char) or char == "_"):
                    itr.put(char)
                    break
                name += char
            res.append(Token(name,pos))
        elif char == "_":
            res.append(Token(char,char.pos))
        else:
            error(f"Unexpected char: {Token(char,char.pos)}")
    return res
    
    
    # TODO
    
    

# TODO all 'for char in itr' loops need an 'else' case for handling depleting the iterator.


# TODO lexer

