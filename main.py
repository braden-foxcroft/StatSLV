

from parser import parse,error
from staticAnalysis import deAlias,addMetadata
import argparse
from collections import defaultdict
from fractions import Fraction
dd = lambda : defaultdict(lambda : Frac(0,1))
Frac = Fraction

parser = argparse.ArgumentParser(description="An interpreter for the StatSLV programming language.")
parser.add_argument('file', action="store",help="The file to run.")
parser.add_argument('--noDiscards', action="store_true",help="Don't discard variables automatically when they are no longer needed.")
parser.add_argument('--reconstruct', action="store_true",help="Display the original program, as interpreted by the parser.")
parser.add_argument('-p',action='store',help="Display the result as a percentage rounded to 'P' decimal places")
parser.add_argument('-f',action='store_true',help="Used if '-p' is present; also print the fractional result.")
parser.add_argument('-silent',action='store_true',help="Don't warn about converting cases to fail or pass.")
args = parser.parse_args()
#print(args)

if args.p != None:
    try:
        args.p = int(args.p)
    except:
        error("Error: '-p' arg was not an int!")

try:
    with open(args.file,"rt",newline='') as file: fileS = file.read()
except:
    error("Error: File could not be opened.")

if args.reconstruct:
    print(deAlias(parse(fileS)).reconstruct())
    exit(0)


class Data:
    """Tracks passes, fails, exits, and returns."""
    def __init__(this):
        this._pass = 0
        this._fail = 0
        this._done = 0
        this._returns = dd()
    def doPass(this,odds):
        this._pass += odds
    def doFail(this,odds):
        this._fail += odds
    def doDone(this,odds):
        this._done += odds
    def doReturn(this,value,odds):
        this._returns[value] += odds


class Contexts:
    """A collection of variable states and their odds of occuring"""
    def __init__(this):
        this._cons = dd()
    def __iter__(this): return iter([(con,this._cons[con]) for con in this._cons])
    def __iadd__(this,con):
        """Takes a tuple,odds pair. Adds it to the dict."""
        con,odds = con # Split into the variable values and the context.
        this._cons[con] += odds
        return this
    def __add__(this,other):
        """Joins two sets of contexts"""
        for con,odds in other:
            this._cons[con] += odds
        return this
    def __repr__(this):
        return repr(this._cons)

def setVar(con,index,val):
    """Set a context var to a value. Returns a new tuple."""
    con = list(con)
    con[index] = val
    return tuple(con)

def runCommand(ast,varLookup,data,conts):
    """Runs an AST Command. takes the AST, a var lookup (staticAnalysis.VarMapping object), a Data object, and a Contexts object.
    Returns a new Contexts, and mutates the data object as needed."""
    if ast.nodeType != "command": raise Exception("Tried to run a non-command!: " + ast.val.raw)
    if ast.val == "select":
        newConts = Contexts()
        var = ast[0].varId
        expr = ast[1]
        cond = ast[2]
        # For each context, apply the select.
        for con,odds in conts:
            # Determine the options for the select
            vals = doEval(expr,con)
            if not isinstance(vals,tuple):
                error("Error: 'select' statement expression returned non-list.\n"+ast.val.line+"\nError at: "+str(ast.val))
            # Generate the new contexts
            newCons = []
            for val in vals:
                newCons.append(setVar(con,var,val))
            # Filter by validity
            newCons2 = []
            for con in newCons:
                valid = doEval(cond,con)
                if valid:
                    newCons2.append(con)
            if len(newCons2) == 0:
                error("Error: 'select' statement had no options!\n"+ast.val.line+"\nError at: "+str(ast.val))
            # Save to the final context
            newOdds = odds * Frac(1,len(newCons2))
            for con in newCons2:
                newConts += con,newOdds
        return newConts
    elif ast.val == "pass":
        for con,odds in conts:
            data.doPass(odds)
        return Contexts()
    elif ast.val == "fail":
        for con,odds in conts:
            data.doFail(odds)
        return Contexts()
    elif ast.val == "done":
        for con,odds in conts:
            data.doDone(odds)
        return Contexts()
    elif ast.val == "return":
        for con,odds in conts:
            res = doEval(ast[0],con)
            data.doReturn(res,odds)
        return Contexts()
    elif ast.val == "for":
        # TODO
        error("'for' not implemented")
    elif ast.val == "if":
        blocks = defaultdict(Contexts) # A dict of block-context pairs. 'None' is the key for otherwise.
        for con,odds in conts:
            i = iter(ast)
            for expr in i:
                block = next(i)
                valid = doEval(expr,con)
                if valid:
                    blocks[block] += con,odds
                    break
            else:
                blocks[None] += con,odds
        newConts = Contexts()
        for block in blocks:
            if block == None:
                newConts = newConts + blocks[block]
                continue
            subConts = blocks[block]
            newSubConts = runBlock(block,varLookup,data,subConts)
            newConts = newConts + newSubConts
        return newConts
    elif ast.val == "bychance":
        newConts = Contexts()
        for con,odds in conts:
            valid = doEval(ast[0],con)
            if not isinstance(valid,int):
                error("Error: 'bychance' statement expression returned non-int.\n"+ast.val.line+"\nError at: "+str(ast.val))
            if valid != 0:
                newConts += con,odds
        return newConts
    elif ast.val == "print":
        toPrint = []
        for con,oddds in conts:
            toPrint.append(str(doEval(ast[0],con)))
        toPrint.sort()
        for t in toPrint:
            print(t)
        return conts
    elif ast.val == "set":
        newConts = Contexts()
        for con,odds in conts:
            res = doEval(ast[2],con)
            con = setVar(con,ast[0].varId,res)
            newConts += con,odds
        return newConts
    
    

def runBlock(ast,varLookup,data,conts):
    """Runs an AST block or program. Takes the AST, a var lookup (staticAnalysis.VarMapping object), a Data object, and a Contexts object.
    Returns a new Contexts, and mutates the data object as needed."""
    for command in ast:
        conts = runCommand(command,varLookup,data,conts)
    return conts


def doEval(ast,cont):
    """Takes an expression and a variable context, and evaluates the expression using the context for variable values.
    Returns the expression result."""
    # TODO
    if ast.nodeType == "expr": return doEval(ast[0],cont)
    if ast.nodeType == "opB":
        if ast.val == "+":
            r1 = doEval(ast[0],cont)
            r2 = doEval(ast[1],cont)
            if isinstance(r1,str) or isinstance(r2,str):
                r1,r2 = str(r1),str(r2)
            return r1 + r2
        if ast.val == "-": return doEval(ast[0],cont) - doEval(ast[1],cont)
        if ast.val == "*": return doEval(ast[0],cont) - doEval(ast[1],cont)
        if ast.val == "//": return doEval(ast[0],cont) // doEval(ast[1],cont)
        if ast.val == "/": return Frac(doEval(ast[0],cont),doEval(ast[1],cont))
        if ast.val == "%": return doEval(ast[0],cont) % doEval(ast[1],cont)
        if ast.val == ",":
            r1 = doEval(ast[0],cont)
            r2 = doEval(ast[1],cont)
            if not isinstance(r1,tuple): r1 = (r1,)
            if not isinstance(r2,tuple): r2 = (r2,)
            return r1 + r2
        if ast.val == "to":
            r1 = doEval(ast[0],cont)
            r2 = doEval(ast[1],cont)
            if not isinstance(r1,int):
                error(f"'to' command recieved non-int input:\n"+ast.val.line)
            if not isinstance(r2,int):
                error(f"'to' command recieved non-int input:\n"+ast.val.line)
            return tuple(range(r1,r2+1))
        if ast.val == "==": return int(doEval(ast[0],cont) == doEval(ast[1],cont))
        if ast.val == "!=": return int(doEval(ast[0],cont) != doEval(ast[1],cont))
        if ast.val == "<=": return int(doEval(ast[0],cont) <= doEval(ast[1],cont))
        if ast.val == ">=": return int(doEval(ast[0],cont) >= doEval(ast[1],cont))
        if ast.val == "<": return int(doEval(ast[0],cont) < doEval(ast[1],cont))
        if ast.val == ">": return int(doEval(ast[0],cont) > doEval(ast[1],cont))
        if ast.val == "or":
            res = doEval(ast[0],cont)
            if res: return res
            return doEval(ast[1],cont)
        if ast.val == "and":
            res = doEval(ast[0],cont)
            if not res: return res
            return doEval(ast[1],cont)
    if ast.nodeType == "opU":
        if ast.val == "-": return -doEval(ast[0],cont)
        if ast.vall == "not": return int(not doEval(ast[0],cont))
    if ast.nodeType == "var": return cont[ast.varId]
    if ast.nodeType == "int": return ast.val.val
    if ast.nodeType == "str": return ast.val.val
    raise Exception(f"Unkown ast node: {ast.nodeType} {ast.val.raw}")


ast = parse(fileS)
ast = deAlias(ast)
ast,varLookup = addMetadata(ast)
d = Data()
c = Contexts()
c += (None,)*len(varLookup),Frac(1,1)

contRes = runBlock(ast,varLookup,d,c)
if d._done != 0:
    if d._returns:
        error("If 'return' is present, programs cannot use 'done' or finish normally!")
    if d._pass and not d._fail:
        if not args.silent: print("All 'done' results marked 'fail'")
        d._done,d._fail = Frac(0,1),d._done
    if d._fail and not d._pass:
        if not args.silent: print("All 'done' results marked 'pass'")
        d._done,d._pass = Frac(0,1),d._done
    if not d._fail and not d._pass:
        error("No passes, fails, or dones!")
if d._returns:
    if d._done or d._pass:
        error("Cannot mix pass/fail and return!")
    print("TODO implement returns")
    exit()
res = Frac(d._pass,d._pass+d._fail)
if args.p != None:
    print(round(float(res*100),args.p),"%",sep="")
if args.p == None or args.f:
    print(res)
exit(0)
