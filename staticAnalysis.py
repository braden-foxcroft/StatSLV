

"""
Important methods:
setColor(bool) determines if the module uses color for console prints.
deAlias(ast) returns an AST without inline 'select' statements.
addMetadata(ast) modifies the AST by adding 'discard' attributes to commands,
    'varId' attributes to 'var' objects, and the 'varCount' attribute to the program root.
"""

# TODO implement '_' and '$' vars
# TODO de-alias 'input' calls
# TODO variable use and declaration of ~inpCount~ variable. Add line at start of program with declaration; remove same line from runner.

from parser import AST,Token,parse,t1,t2,t3
from collections import deque
from color import *
# Token(raw,pos,line,val=None)
# AST(root : Token, children : [AST], type : str)

# A file for carrying out static analysis. Modifies the AST to be easier to execute, and to track when variables should vanish.

def showDiscards(exampleStr):
    """Shows the static analysis info from code, for discards only"""
    p,m = addMetadata(deAlias(parse(exampleStr)))
    print(red("discards:"))
    print(p.reconstruct(funcArg = lambda n:n.discards or None))

def testExample(exampleStr):
    """Shows the static analysis info from the code, so you can see how things worked"""
    p,m = addMetadata(deAlias(parse(exampleStr)))
    print(red("code:"))
    print(p.reconstruct())
    print(red("prevs:"))
    print(p.reconstruct(funcArg = lambda n:[prev.val.raw for prev in n.prevs] or None))
    print(red("varsUsed:"))
    print(p.reconstruct(funcArg = lambda n:n.varsUsed or None))
    print(red("varsMade:"))
    print(p.reconstruct(funcArg = lambda n:n.varsMade or None))
    print(red("varsNeeded:"))
    print(p.reconstruct(funcArg = lambda n:n.varsNeeded or None))
    print(red("discards:"))
    print(p.reconstruct(funcArg = lambda n:n.discards or None))
    #print(red("discards (int):"))
    #print(p.reconstruct(funcArg = lambda n:n.discardsInt or None))


# Code for de-aliasing below.
def deAlias(ast):
    """A function which removes aliases from an AST.
    At the moment, only affects 'select' function/unary operator calls."""
    return ast.modify(deAliasSelect)

def deAliasSelect(ast):
    """Takes an command AST node. Returns a list of command AST nodes, where any in-line 'select' calls are split onto previous lines."""
    newChildren = [] # The new children
    res = [] # A list of var-expr pairs, where 'select var from expr' needs to be added before the command.
    nextFree = 0 # The next free ~1~ var name to use.
    # An AST node representing 'True' for the purposes of a 'select' statement.
    trueAst = AST(Token("expr",ast.val.pos,"'select' statement macro put on separate line."),[AST(Token("1",ast.val.pos,val=1),[],"int")],"expr")
    # Go through and modify the AST.
    for child in ast:
        if child.nodeType == "expr":
            newChild,toSelectAdd,nextFree = deAliasExpr(child,nextFree,child,trueAst)
            newChildren.append(newChild)
            res += toSelectAdd
        else:
            newChildren.append(child)
    res.append(AST(ast.val,newChildren,"command"))
    return res

def deAliasExpr(node,nextFree,exprRoot,trueAst):
    """A recursive function which de-aliases expressions.
    takes an AST (expr or sub-expr) and an int (saying what ~number~ var is free next).
        Also takes an "expr" ast root, used for generating new expr nodes as needed.
    Returns a new AST, a list of var-expr pairs to select, and a new int."""
    if node.nodeType == "opU" and node.val == "select":
        expr,pairs,nextFree = deAliasExpr(node[0],nextFree,exprRoot,trueAst)
        var = AST(Token(f"~{nextFree}~",node.val.pos,"System-generated line"),[],"var")
        expr = AST(exprRoot.val,[expr],"expr")
        newNode = AST(Token("select",var.val.pos,f"select {var} from {expr.reconstruct(0)}"),[var,expr,trueAst],"command")
        pairs.append(newNode)
        return var,pairs,nextFree+1
    # TODO modify to support de-aliasing 'input' too.
    if node.nodeType == "opU" and node.val == "input":
        expr,pairs,nextFree = deAliasExpr(node[0],nextFree,exprRoot,trueAst)
        var = AST(Token(f"~{nextFree}~",node.val.pos,"System-generated line"),[],"var")
        expr = AST(exprRoot.val,[expr],"expr")
        newNode = AST(Token("input",var.val.pos,f"input {var} {expr.reconstruct(0)}"),[var,expr],"command")
        pairs.append(newNode)
        return var,pairs,nextFree+1
    children = []
    pairs = []
    for child in node:
        newChild,newPairs,nextFree = deAliasExpr(child,nextFree,exprRoot,trueAst)
        children.append(newChild)
        pairs += newPairs
    return AST(node.val,children,node.nodeType),pairs,nextFree


def findVarNames(ast):
    """Takes an ast, returns a sorted non-repeating list of var names."""
    varList = ast.filter(lambda node : node.nodeType == "var")
    varSet = set([var.val.raw for var in varList])
    varSet = (varSet - {"_"}) | {"~inpCount~","$"}
    return sorted(varSet)
    
class VarMapping:
    """A class which maps vars to ints, and vice-versa.
    To construct, provide a non-duplicated list of vars.
    To use, provide obj[var] or obj[int] to get the corresponding value."""
    def __init__(this,varList):
        d = dict()
        for i in range(0,len(varList)):
            d[varList[i]] = i
            d[i] = varList[i]
            # Note: no conflict because vars are str and ints are int.
        this._dict = d
        this._len = len(varList)
    def __getitem__(this,item): return this._dict[item]
    def __len__(this): return this._len

class Queue:
    def __init__(this):
        this._q = deque()
    def push(this,val):
        this._q.append(val)
    def pop(this):
        return this._q.popleft()
    def __len__(this): return len(this._q)
    def __iadd__(this,vals):
        """Adds multiple values to the queue. Uses any iterable, except an AST"""
        if isinstance(vals,AST): raise Exception("Attemped to += an AST to a queue")
        for val in vals:
            this.push(val)
        return this
    def __repr__(this):
        return "Queue(" + repr(this._q) + ")"
    def __bool__(this): return len(this) > 0
    def __contains__(this,val): return val in this._q

def tagVars(m):
    """Takes an ast and VarMapping,
    modifies the ast so that vars have an 'varId' tag corresponding to the var number.
    Takes a mapping, returns a function which modifies and AST"""
    def mapVals(ast):
        if ast.nodeType != "var": return
        ast.varId = m[ast.val.raw]
        return
    return mapVals

def addCommandDefaults(ast):
    """Takes an AST node, and if it's a command, adds:
    prevs : set, # The AST command nodes which can run immediately before.
    nexts : set, # The AST command nodes which can run immediately after.
    varsUsed : set, # The vars used by this command
    varsNeeded : set, # The vars which have to be retained after this command finishes.
    varsHad : set, # The vars which may exist at this moment in time.
    varsMade : set, # The vars created directly by this specific line of code
    discards : set # The vars which exist and don't need to at this moment in time."""
    if ast.nodeType != "command": return
    ast.prevs = set()
    ast.nexts = set()
    ast.varsUsed = set()
    ast.varsNeeded = set()
    ast.varsHad = set()
    ast.varsMade = set()
    ast.discards = set()
    ast.discardsInt = set()
    return

def varUseAndAssign(ast):
    """Takes an AST, and if its a command, populates the varsUsed and varsMade values"""
    if ast.nodeType != "command": return
    # varsUsed
    varsUsed = []
    for child in ast:
        if child.nodeType == "expr":
            varsUsed += child.filter(lambda node : node.nodeType == "var")
    varsUsed = [var.val.raw for var in varsUsed]
    ast.varsUsed = set(varsUsed)
    # varsMade
    varsMade = []
    if ast.val in ["set","select","for"]:
        varsMade.append(ast[0].val.raw)
    elif ast.val == "select":
        varsMade.append(ast[0].val.raw)
    ast.varsMade = set(varsMade)
    ast.varsMade = ast.varsMade - {"$","_"}
    return



def determinePrevs(ast,prev=set()):
    """Takes an AST, modifies the 'prevs' values so that each command knows what can precede the command.
    Optionally takes the previous command list, if available.
    Returns a list of the commands which can happen at the end of this command.
    (For simple commands, it is just iself. For more complicated commands, it may be the command plus the last command in each block.)"""
    if ast.nodeType == "program" or ast.nodeType == "block":
        nexts = prev
        for command in ast:
            command.prevs |= nexts
            nexts = determinePrevs(command)
        return nexts
    if ast.val == "if":
        res = {ast}
        for child in ast:
            if child.nodeType != "block": continue
            res |= determinePrevs(child,{ast})
        return res
    if ast.val == "for":
        # 'for' prev for end of block is start of block
        res = {ast}
        block = ast[2]
        blockNexts = determinePrevs(block,{ast})
        if len(block) > 0:
            block[0].prevs |= blockNexts
        return res | blockNexts
    if ast.val in ["pass","fail","return","done"]:
        return set()
    return {ast}
    
def setNexts(ast):
    """Sets nexts of prev commands."""
    if ast.nodeType != "command": return
    for nxt in ast.prevs:
        nxt.nexts |= {ast}
    return

def getVarsNeeded(ast):
    """Populates 'varsNeeded' for all commands in an AST"""
    q = Queue()
    q += ast.filter(lambda node: node.nodeType == "command")
    while q:
        com = q.pop()
        varsHere = com.varsUsed | (com.varsNeeded - com.varsMade)
        # Add each var for each prev. If a var is added, prev is also added to the queue, if not present.
        for var in varsHere:
            for prev in com.prevs:
                if var not in prev.varsNeeded:
                    prev.varsNeeded |= {var}
                    if prev not in q: q.push(prev)
    return

def getVarsHad(ast):
    """Populates 'varsHad' and 'discards' for all commands in an AST"""
    q = Queue()
    q += ast.filter(lambda node: node.nodeType == "command")
    while q:
        com = q.pop()
        varsHad = com.varsHad | com.varsMade
        com.discards |= (varsHad - com.varsNeeded)
        com.varsHad = varsHad & com.varsNeeded
        # Add each var for each prev. If a var is added, prev is also added to the queue, if not present.
        for var in com.varsHad:
            for nxt in com.nexts:
                if var not in nxt.varsHad:
                    nxt.varsHad |= {var}
                    if nxt not in q: q.push(nxt)
    return

def getIntDiscards(ast,m):
    """Takes an AST and a mapper. Adds int version of discards to each needed node."""
    for node in ast.filter(lambda node: node.nodeType == "command"):
        for disc in node.discards:
            node.discardsInt.add(m[disc])
    return



def addMetadata(ast):
    """modifies the AST by adding 'discard' attributes to commands,
    'varId' attributes to 'var' objects, and the 'varCount' attribute to the program root.
    Adds 'jump' tag to tell where each 'break' or 'continue' ends up.
    Returns the ast and the mapping."""
    varNames = findVarNames(ast)
    m = VarMapping(varNames)
    ast.forAll(tagVars(m))
    ast.varCount = len(m)
    # Overall task: calculate the discard values.
    ast.forAll(addCommandDefaults)
    # Get the vars used on each line, and which are assigned. Ignore '_' and '$'
    ast.forAll(varUseAndAssign)
    # Figure out which lines precede which lines. Note that 'for' loops have unconventional ordering.
    determinePrevs(ast)
    # Add 'nexts' based on the 'prevs'
    ast.forAll(setNexts)
    # determines varsNeeded.
    getVarsNeeded(ast)
    # determines varsHad, discards
    getVarsHad(ast)
    getIntDiscards(ast,m)
    return ast,m





