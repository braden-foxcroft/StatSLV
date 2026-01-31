#! /usr/bin/python3

from parser import parse,error
from staticAnalysis import deAlias,addMetadata,testExample,showDiscards
import argparse
from collections import defaultdict
from fractions import Fraction
from color import *
dd = lambda : defaultdict(Frac)
Frac = Fraction

import sys
import os
os.system("") # Turns on color codes, if needed. A hacky solution, though.

parser = argparse.ArgumentParser(description="An interpreter for the StatSLV programming language.")
parser.add_argument('file', action="store",help="The file to run.")

ParserDisp = parser.add_argument_group('Output display options')
ParserDisp.add_argument('-p',action='store_true',help="Display the result as a percentage")
ParserDisp.add_argument('-P',action='store',help="Display the result as a percentage rounded to 'P' decimal places",type=int)
ParserDisp.add_argument('-d',action='store_true',help="Display the result as a decimal")
ParserDisp.add_argument('-D',action='store',help="Display the result as a decimal rounded to 'D' decimal places",type=int)
ParserDisp.add_argument('-f',action='store_true',help="Print the fractional result. (Default if all options omitted.)")
ParserDisp.add_argument('-F',action='store',help="Print the fractional result. (round to the nearest fraction with a denominator <= the value provided)",type=int)
ParserDisp.add_argument('-b',action='store_true',help="Print the fractional result as a beautiful, multi-line fraction.")
ParserDisp.add_argument('-B',action='store',help="Print the fractional result as a beautiful, multi-line fraction. (round to the nearest fraction with denominator <= the value provided)",type=int)

ParserPrint = parser.add_argument_group('Print default options')
ParserPrint.add_argument('-printa',"-pa",action='store_true',help="'print' will be treated like 'printa'. This is the default.")
ParserPrint.add_argument('-printc',"-pc",action='store_true',help="'print' will be treated like 'printc'.")
ParserPrint.add_argument('-printr',"-pr",action='store_true',help="'print' will be treated like 'printr'.")


parserExtraDisp = parser.add_argument_group('Additional display options')
parserExtraDisp.add_argument('-silent','-s',action='store_true',help="Don't warn about converting cases to fail or pass.")
parserExtraDisp.add_argument('-noAgg','-na',action='store_true',help="Don't aggregate print statements. Aggregation is when it adds (3x) in front of a result instead of printing it 3 times.")
parserExtraDisp.add_argument('-intAllowed','-i',action='store_true',help="Fractions will be displayed as integers whenever possible.")
parserExtraDisp.add_argument('-NoColor','-nc',action='store_true',help="Don't include ANSI color codes in printouts.")
parserExtraDisp.add_argument('-isatty','-tty',action='store_true',help="Assume the input and output are terminals. This may resolve issues with displaying color.")
parserExtraDisp.add_argument('-noGreyFill','-ng',action='store_true',help="When getting input: if the input has already been obtained, then don't display it in grey.")
parserExtraDisp.add_argument('-skipInp','-ni',action='store_true',help="When getting input: if the input has already been obtained, then silently use it.")

parserDebug = parser.add_argument_group('Debug options')
parserDebug.add_argument('-DebugNoDiscards','-nd', action="store_true",help="Don't discard variables automatically when they are no longer needed.")
parserDebug.add_argument('-DebugStaticAnalysis','-dsa', action="store_true",help="Show a debug of the program in various stages of static analysis.")
parserDebug.add_argument('-DebugDiscards','-dd', action="store_true",help="Show a debug of the discards of the program")
parserDebug.add_argument('-DebugReconstruct','-dr', action="store_true",help="Display the original program, as interpreted by the parser.")
parserDebug.add_argument('-DebugAST','-da', action="store_true",help="Display the Raw AST")

args = parser.parse_args()
#print(args)

# Set default for args.f if all options are omitted.
if not (args.p or args.P != None or args.d or args.D != None or args.f or args.F != None or args.b or args.B != None):
    args.f = True


# No discards
nd = args.DebugNoDiscards


if args.NoColor or (not sys.stdout.isatty() and not args.isatty):
    Color.doColor = False



try:
    with open(args.file,"rt",newline='') as file: fileS = file.read()
except:
    error("Error: File could not be opened.")

if args.DebugReconstruct:
    print(deAlias(parse(fileS)).reconstruct())
    exit(0)
if args.DebugStaticAnalysis:
    testExample(fileS)
    exit(0)
if args.DebugDiscards:
    showDiscards(fileS)
    exit(0)
if args.DebugAST:
    print(deAlias(parse(fileS)))
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
    def assign(this,var,val):
        """Creates a new context, assigning the val to the var. Takes the var as an int."""
        c = Contexts()
        for con,odds in this:
            c += setVar(con,var,val),odds
        return c
    def discard(this,setInts):
        """Takes a set of integer vars to delete. Sets them to 'None'."""
        if setInts == set() or nd:
            return this
        c = Contexts()
        for con,odds in this:
            for var in setInts:
                con = setVar(con,var,None)
            c += con,odds
        return c

gottenInput = []
def doInput(prompt,count):
    fromFile = (not sys.stdin.isatty() and not args.isatty)
    if prompt.endswith(":"):
        prompt = prompt + " "
    elif prompt.endswith(" ") or prompt.endswith("="):
        prompt = prompt # Do nothing
    else:
        prompt = prompt + "\n> "
    if count < len(gottenInput):
        res = gottenInput[count]
        if args.skipInp:
            autoInp = False
        else:
            print(prompt,end="")
            autoInp = True
    elif fromFile and args.skipInp:
        res = input("") # No input text
        gottenInput.append(res)
        autoInp = False
    else:
        res = input(prompt)
        gottenInput.append(res)
        autoInp = fromFile
    if autoInp:
        if args.noGreyFill:
            print("") # End the input line.
        else:
            print(grey(res))
    # Try returning as an int, otherwise a frac, otherwise a str.
    try:
        return int(res)
    except:
        try:
            return Fraction(res)
        except:
            return res



def setVar(con,index,val):
    """Set a context var to a value. Returns a new tuple."""
    if index == None or con[index] == val: return con
    con = list(con)
    con[index] = val
    return tuple(con)

def stringSortKey(s):
        """Turns a string into a (len(str),str) pair, ensuring short strings are before long strings when sorting.
        If the string is an int, float, or fraction, returns the converted value followed by the str."""
        try:
            return Fraction(s),s
        except:
            try:
                return int(s),s
            except:
                    try:
                        return float(s),s
                    except:
                        return len(s),s

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
            vals = doEval(expr,con,odds)
            if not isinstance(vals,tuple):
                error("Error: 'select' statement expression returned non-list.\n"+ast.val.line+"\nError at: "+str(ast.val))
            # Generate the new contexts
            newCons = []
            for val in vals:
                newCons.append(setVar(con,var,val))
            # Filter by validity
            newCons2 = []
            for con in newCons:
                valid = doEval(cond,con,odds)
                if valid:
                    newCons2.append(con)
            if len(newCons2) == 0:
                error("Error: 'select' statement recieved an empty list of options!\n"+ast.val.line+"\nError at: "+str(ast.val))
            # Save to the final context
            newOdds = odds * Frac(1,len(newCons2))
            for con in newCons2:
                newConts += con,newOdds
        return newConts.discard(ast.discardsInt)
    elif ast.val == "nop":
        return conts
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
            res = doEval(ast[0],con,odds)
            data.doReturn(res,odds)
        return Contexts()
    elif ast.val == "for":
        blocks = defaultdict(Contexts) # A dict of block-context pairs. 'None' is the key for otherwise.
        for con,odds in conts:
            # Find range
            rng = doEval(ast[1],con,odds)
            if not isinstance(rng,tuple):
                error("'for' loop expr did not return list:\n"+var.val.line)
            blocks[rng] += con,odds
        newConts = Contexts()
        for block in blocks:
            subConts = blocks[block]
            for i in block:
                # Don't assign var if it will just be instantly deleted.
                if ast[0].varId in ast.discardsInt:
                    subConts = subConts.discard(ast.discardsInt)
                else:
                    subConts = subConts.assign(ast[0].varId,i).discard(ast.discardsInt)
                subConts = runBlock(ast[2],varLookup,data,subConts)
            newConts = newConts + subConts
        return newConts
    elif ast.val == "bychance":
        newConts = Contexts()
        for con,odds in conts:
            valid = doEval(ast[0],con,odds)
            if not isinstance(valid,int):
                error("Error: 'bychance' statement expression returned non-int.\n"+ast.val.line+"\nError at: "+str(ast.val))
            if valid != 0:
                newConts += con,odds
        return newConts.discard(ast.discardsInt)
    elif ast.val == "if":
        blocks = defaultdict(Contexts) # A dict of block-context pairs. 'None' is the key for otherwise.
        for con,odds in conts:
            i = iter(ast)
            for expr in i:
                block = next(i)
                valid = doEval(expr,con,odds)
                if valid:
                    blocks[block] += con,odds
                    break
            else:
                blocks[None] += con,odds
        newConts = Contexts()
        for block in blocks:
            if block == None:
                newConts = newConts + blocks[block].discard(ast.discardsInt)
                continue
            subConts = blocks[block].discard(ast.discardsInt)
            newSubConts = runBlock(block,varLookup,data,subConts)
            newConts = newConts + newSubConts
        return newConts
    elif ast.val == "printc" or (ast.val == "print" and args.printc):
        # Print each item, tracking count.
        toPrint = []
        for con,odds in conts:
            toPrint.append(str(doEval(ast[0],con,odds)))
        toPrintAgg = defaultdict(int)
        maxLen = 0
        for val in toPrint:
            toPrintAgg[val] += 1
            newLen = len(str(toPrintAgg[val]))
            if newLen > maxLen: maxLen = newLen
        keys = sorted(set(toPrint),key=stringSortKey)
        if keys == [""]:
            print()
        else:
            if args.noAgg:
                toPrint.sort(key=stringSortKey)
                for t in toPrint:
                    print(t)
            else:
                for key in keys:
                    print(f"({str(toPrintAgg[key]).rjust(newLen)}x)    " + key)
        return conts.discard(ast.discardsInt)
    elif ast.val == "printr" or (ast.val == "print" and args.printr):
        # Print each item, tracking likelyhood. Use the likelyhood given that the print statement occured, not the absolute likelyhood.
        toPrint = defaultdict(Fraction)
        totalOdds = Fraction(0)
        for con,odds in conts:
            toPrint[str(doEval(ast[0],con,odds))] += odds
            totalOdds += odds
        keys = sorted(toPrint,key=stringSortKey)
        if keys == [""]:
            print()
        elif args.noAgg:
            for key in keys:
                print(key)
        else:
            maxLen = 0
            for key in keys:
                maxLen = max(maxLen, len(str(toPrint[key] / totalOdds)))
            for key in keys:
                print(f"({str(toPrint[key] / totalOdds).rjust(maxLen)})    {key}")
        return conts.discard(ast.discardsInt)
    elif ast.val == "printa" or ast.val == "print":
        # Print each item, tracking the absolute probability of the print occurring at this moment in time.
        toPrint = defaultdict(Fraction)
        for con,odds in conts:
            toPrint[str(doEval(ast[0],con,odds))] += odds
        keys = sorted(toPrint,key=stringSortKey)
        if keys == [""]:
            print()
        elif args.noAgg:
            for key in keys:
                print(key)
        else:
            maxLen = 0
            for key in keys:
                maxLen = max(maxLen, len(str(toPrint[key])))
            for key in keys:
                print(f"({str(toPrint[key]).rjust(maxLen)})    {key}")
        return conts.discard(ast.discardsInt)
    elif ast.val == "set":
        newConts = Contexts()
        for con,odds in conts:
            res = doEval(ast[2],con,odds)
            con = setVar(con,ast[0].varId,res)
            newConts += con,odds
        return newConts.discard(ast.discardsInt)
    elif ast.val == "input":
        newConts = Contexts()
        inpCountId = varLookup["~inpCount~"]
        allDisps = defaultdict(list)
        for con,odds in conts:
            toDisp = doEval(ast[1],con,odds)
            inpCount = con[inpCountId]
            allDisps[(toDisp,inpCount)].append((setVar(con,inpCountId,con[inpCountId]+1),odds))
        keys = sorted(allDisps)
        for toDisp,inpCount in keys:
            res = doInput(toDisp,inpCount)
            for con,odds in allDisps[toDisp,inpCount]:
                newConts += setVar(con,ast[0].varId,res),odds
        return newConts
    else:
        error(f"error in runCommand: unknown command: {orange(ast.val.val)}")
    error(f"No return value for runCommand: {orange(ast.val.val)}")



def runBlock(ast,varLookup,data,conts):
    """Runs an AST block or program. Takes the AST, a var lookup (staticAnalysis.VarMapping object), a Data object, and a Contexts object.
    Returns a new Contexts, and mutates the data object as needed."""
    for command in ast:
        conts = runCommand(command,varLookup,data,conts)
    return conts


def doEval(ast,cont,odds):
    """Takes an expression and a variable context, and evaluates the expression using the context for variable values.
    Returns the expression result."""
    # TODO type validation, list operations.
    if ast.nodeType == "expr":
        return doEval(ast[0],cont,odds)
    if ast.nodeType == "opB":
        if ast.val == "+":
            r1 = doEval(ast[0],cont,odds)
            r2 = doEval(ast[1],cont,odds)
            if isinstance(r1,str) or isinstance(r2,str):
                r1,r2 = str(r1),str(r2)
            return r1 + r2
        if ast.val == "-": return doEval(ast[0],cont,odds) - doEval(ast[1],cont,odds)
        if ast.val == "*": return doEval(ast[0],cont,odds) * doEval(ast[1],cont,odds)
        if ast.val == "//": return doEval(ast[0],cont,odds) // doEval(ast[1],cont,odds)
        if ast.val == "/": return Frac(doEval(ast[0],cont,odds),doEval(ast[1],cont,odds))
        if ast.val == "%": return doEval(ast[0],cont,odds) % doEval(ast[1],cont,odds)
        if ast.val == ",":
            r1 = doEval(ast[0],cont,odds)
            r2 = doEval(ast[1],cont,odds)
            if not isinstance(r1,tuple): r1 = (r1,)
            if not isinstance(r2,tuple): r2 = (r2,)
            return r1 + r2
        if ast.val == "to":
            r1 = doEval(ast[0],cont,odds)
            r2 = doEval(ast[1],cont,odds)
            if not isinstance(r1,int):
                error(f"'to' operator recieved non-int input:\n"+ast.val.line)
            if not isinstance(r2,int):
                error(f"'to' operator recieved non-int input:\n"+ast.val.line)
            return tuple(range(r1,r2+1))
        if ast.val == "==": return int(doEval(ast[0],cont,odds) == doEval(ast[1],cont,odds))
        if ast.val == "!=": return int(doEval(ast[0],cont,odds) != doEval(ast[1],cont,odds))
        if ast.val == "<=": return int(doEval(ast[0],cont,odds) <= doEval(ast[1],cont,odds))
        if ast.val == ">=": return int(doEval(ast[0],cont,odds) >= doEval(ast[1],cont,odds))
        if ast.val == "<": return int(doEval(ast[0],cont,odds) < doEval(ast[1],cont,odds))
        if ast.val == ">": return int(doEval(ast[0],cont,odds) > doEval(ast[1],cont,odds))
        if ast.val == "or":
            res = doEval(ast[0],cont,odds)
            if res: return res
            return doEval(ast[1],cont,odds)
        if ast.val == "and":
            res = doEval(ast[0],cont,odds)
            if not res: return res
            return doEval(ast[1],cont,odds)
        if ast.val == "in":
            r1 = doEval(ast[0],cont,odds)
            r2 = doEval(ast[1],cont,odds)
            if not isinstance(r2,tuple):
                error(f"'in' operator recieved non-list input on right:\n"+ast.val.line)
            return int(r1 in r2)
        if ast.val == ".":
            r1 = doEval(ast[0],cont,odds)
            r2 = doEval(ast[1],cont,odds)
            if not isinstance(r1,Frac) and not isinstance(r1,int):
                error(f"'.' operator recieved non-numeric input on left:\n"+ast.val.line)
            if not isinstance(r2,int):
                error(f"'.' operator recieved non-int input on right:\n"+ast.val.line)
            return str(round(float(r1),r2))
    if ast.nodeType == "opU":
        if ast.val == "-": return -doEval(ast[0],cont,odds)
        if ast.val == "not": return int(not doEval(ast[0],cont,odds))
        if ast.val == "sorted":
            r1 = doEval(ast[0],cont,odds)
            if not isinstance(r1,tuple):
                error(f"'sorted' function recieved non-tuple input:\n"+ast.val.line)
            return tuple(sorted(r1))
    if ast.nodeType == "var":
        if ast.val.raw == "$": return odds
        if ast.varId == None: return None
        return cont[ast.varId]
    if ast.nodeType == "int": return ast.val.val
    if ast.nodeType == "str": return ast.val.val
    if ast.nodeType == "list": return ast.val.val
    raise Exception(f"Unkown ast node: {ast.nodeType} {ast.val.raw}")


ast = parse(fileS)
ast = deAlias(ast)
ast,varLookup = addMetadata(ast)
d = Data()
c = Contexts()
c += setVar((None,)*len(varLookup),varLookup["~inpCount~"],0),Frac(1,1)

def strFrac(res, returnInstead=False):
    """Returns a Fraction as a colored fraction str."""
    if not isinstance(res,Fraction):
        error(f"printFrac expected a Fraction, got {yellow(type(res))} {red(res)} instead.")
    if args.intAllowed and res.is_integer():
        return col_int(int(res))
    return col_int(res.numerator) + "/" + col_int(res.denominator)

def floatOrInt(res):
    """Converts a Fraction to a float or int, depending on command-line args and if it is possible to do so."""
    if res.is_integer(): return int(res)
    return float(res)

def padEven(a,b):
    """Adds a '0' at the start of the shorter string if the strings' oddness/evenness doesn't match.
    Returns both strings."""
    if len(a) % 2 == len(b) % 2:
        return a,b
    if len(a) > len(b):
        a,"0"+b
    return "0"+a,b

def printNiceFrac(res):
    """Print a Fraction as a multi-line fraction."""
    num = res.numerator
    den = res.denominator
    num = str(num)
    den = str(den)
    num,den = padEven(num,den)
    maxLen = max(len(num),len(den))
    print("\n" + col_int(num.center(maxLen+4)) +"\n" + "─"*(maxLen+4) + "\n" + col_int(den.center(maxLen+4)))
    
    
def showAgg(res):
    # Takes a dict (str -> odds). Prints it line-by-line, with each line having the format:
    # (odds) item 
    keys = list(res)
    keys.sort(key=stringSortKey)
    maxLen = 0
    for key in keys:
        maxLen = max(maxLen,len(str(key)))
    for key in keys:
        print(f"({str(res[key]).rjust(maxLen)}) {str(key)}")

    

def showResult(res):
    """Shows the result (Fraction object) using the global 'args' variable to format it correctly.
    May print multiple lines if multiple argument flags are provided."""
    if args.p:
        print(col_int(floatOrInt(res*100)),"%",sep="")
    if args.P != None:
        print(col_int(round(floatOrInt(res*100),args.P)),"%",sep="")
    if args.d:
        print(col_int(floatOrInt(res)))
    if args.D:
        print(col_int(round(floatOrInt(res),args.D)))
    if args.f:
        print(strFrac(res))
    if args.F != None:
        print(strFrac(res.limit_denominator(args.F)))
    if args.b:
        printNiceFrac(res)
    if args.B != None:
        printNiceFrac(res.limit_denominator(args.B))



contRes = runBlock(ast,varLookup,d,c)


if d._returns:
    if d._done or d._pass or d._fail:
        error("If 'return' is present, pass/fail/done cannot be used!\n(If you want a path to finish without returning, use 'bychance 0' instead.)")
    returns = d._returns
    if list(returns) == [""]: exit(0) # TODO document.
    allNums = True
    for r in returns:
        if not isinstance(r,int) and not isinstance(r,Fraction):
            allNums = False
    if allNums:
        res = Frac(0)
        odds = Frac(0)
        for val in returns:
            res += returns[val] * val
            odds += returns[val]
        res = res / odds
        showResult(res)
    else:
        res = defaultdict(Fraction)
        for key in returns:
            res[str(key)] += returns[key]
        showAgg(res)
else:
    if d._done != 0:
        if d._pass and not d._fail:
            if not args.silent: print(f"All {yellow('unmarked')} results marked as {red('fail')}")
            d._done,d._fail = Frac(0,1),d._done
        elif d._fail and not d._pass:
            if not args.silent: print(f"All {yellow('unmarked')} results marked as {green('pass')}")
            d._done,d._pass = Frac(0,1),d._done
        elif d._fail and d._pass:
            error(f"The code mixes the use of {green('pass')}, {red('fail')}, and {yellow('done')}.\n({yellow('done')} is insterted automatically after the final line of the code, to catch any cases where the code doesn't {green('pass')} or {red('fail')} first.)\nPlease make sure that your code always finishes with a {green('pass')} or {red('fail')}!")
    if d._pass + d._fail == 0:
        if args.silent:
            exit(1)
        else:
            error("No result.")
    res = Frac(d._pass,d._pass+d._fail)
    showResult(res)

