

"""

"""

from parser import AST,Token,parse,t1,t2,t3
# Token(raw,pos,line,val=None)
# AST(root : Token, children : [AST], type : str)

# A file for carrying out static analysis. Modifies the AST to be easier to execute, and to track when variables should vanish.

# TODO move 'select' function calls to separate lines,
# TODO code for figuring out which lines run before/after which lines,
# code for tracking variable use, add 'discard' attribute to command nodes for when variables are no longer used.
# TODO aggregate all var names, add mapping of var names to integers.

color = False
def setColor(newColor=True):
    """Determines if functions in this module use color when generating text."""
    global color
    color = newColor
# TODO implement color in this module.

def deAlias(ast):
    """A function which removes aliases from an AST.
    At the moment, only affects 'select' function/unary operator calls."""
    return ast.modify(deAliasSelect)

def deAliasSelect(ast):
    newChildren = [] # The new children
    toSelect = [] # A list of var-expr pairs, where 'select var from expr' needs to be added before the command.
    nextFree = 0 # The next free ~1~ var name to use.
    for child in ast:
        if child.nodeType == "expr":
            newChild,toSelectAdd,nextFree = deAliasExpr(child,nextFree,child)
            newChildren += newChild
            toSelect += toSelectAdd
        else:
            newChildren.append(child)
    res = []
    trueAst = AST(Token("expr",ast.val.pos,"'select' statement macro put on separate line."),[AST(Token("1",ast.val.pos,val=1),[],"int")],"expr")
    for var,expr in toSelect:
        res.append(AST(Token("select",var.val.pos,f"select ({var}) from {expr.reconstruct(color,0)}"),[var,expr,trueAst],"command"))
    res.append(AST(ast.val,newChildren,"command"))
    return res




def deAliasExpr(node,nextFree,exprRoot):
    """A recursive function which de-aliases expressions.
    takes an AST (expr or sub-expr) and an int (saying what ~number~ var is free next).
        Also takes an "expr" ast root, used for generating new expr nodes as needed.
    Returns a new AST, a list of var-expr pairs to select, and a new int."""
    if node.nodeType == "opU" and node.val == "select":
        expr,pairs,nextFree = deAliasExpr(node[0],nextFree,exprRoot)
        var = AST(Token(f"~{nextFree}~",node.val.pos,"System-generated line"),[],"var")
        pairs.append([var,AST(exprRoot.val,[expr],"expr")])
        return var,pairs,nextFree+1
    children = []
    pairs = []
    for child in node:
        newChild,newPairs,nextFree = deAliasExpr(child,nextFree,exprRoot)
        children.append(newChild)
        pairs += newPairs
    return AST(node.val,children,node.nodeType),pairs,nextFree


