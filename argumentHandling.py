
import argparse
from parser import error


def showArg(helpMessage,show):
    """Either returns the original help message, or a constant telling argparse to not show help for the arg"""
    if show: return helpMessage
    return argparse.SUPPRESS

def parseArgs(argList,noFileNeeded=False):
    """Parses a list of arguments, like sys.argv[1:]. You can tell it to skip the file argument, if desired"""

    argsIO = False
    argsGraph = False
    argsDebug = False
    argsCommon = True
    if "-ho" in argList:
        argsIO = True
        argsCommon = False
    if "-hg" in argList:
        argsGraph = True
        argsCommon = False
    if "-hd" in argList:
        argsDebug = True
        argsCommon = False
    if "-H" in argList:
        argsIO = True
        argsGraph = True
        argsDebug = True
        argsCommon = True


    parser = argparse.ArgumentParser(description="An interpreter for the StatSLV programming language.")
    parser.add_argument('file', action="store",help="The file to run.",default=None,nargs="?")
    parser.add_argument('-H',action="store_true",help=showArg("Shows help for ALL command-line flags",argsCommon))
    parser.add_argument('-ho',action="store_true",help=showArg("Shows help for command-line flags for command-line input and output",argsCommon or argsIO))
    parser.add_argument('-hg',action="store_true",help=showArg("Shows help for command-line flags for graph output",argsCommon or argsGraph))
    parser.add_argument('-hd',action="store_true",help=showArg("Shows help for command-line flags for debugging",argsCommon or argsDebug))

    ParserDisp = parser.add_argument_group('Output display options')
    ParserDisp.add_argument('-p',action='store_true',help=showArg("Display the result as a percentage",argsCommon or argsIO))
    ParserDisp.add_argument('-P',action='store',help=showArg("Display the result as a percentage rounded to 'P' decimal places",argsCommon or argsIO),type=int)
    ParserDisp.add_argument('-d',action='store_true',help=showArg("Display the result as a decimal",argsCommon or argsIO))
    ParserDisp.add_argument('-D',action='store',help=showArg("Display the result as a decimal rounded to 'D' decimal places",argsCommon or argsIO),type=int)
    ParserDisp.add_argument('-f',action='store_true',help=showArg("Print the fractional result. (Default if all options omitted.)",argsIO))
    ParserDisp.add_argument('-F',action='store',help=showArg("Print the fractional result. (round to the nearest fraction with a denominator <= the value provided)",argsIO),type=int)
    ParserDisp.add_argument('-b',action='store_true',help=showArg("Print the fractional result as a beautiful (?), multi-line fraction.",argsIO))
    ParserDisp.add_argument('-B',action='store',help=showArg("Print the fractional result as a beautiful (?), multi-line fraction. (round to the nearest fraction with denominator <= the value provided)",argsIO),type=int)

    ParserPrint = parser.add_argument_group('Print default options')
    ParserPrint.add_argument('-printa',"-pa",action='store_true',help=showArg("'print' will be treated like 'printa' (show absolute probablilty for print to occur). This is the default.",argsIO))
    ParserPrint.add_argument('-printc',"-pc",action='store_true',help=showArg("'print' will be treated like 'printc'. (show count for how many times it printed)",argsIO))
    ParserPrint.add_argument('-printr',"-pr",action='store_true',help=showArg("'print' will be treated like 'printr'. (show relative probability for print to occur.)",argsIO))
    ParserPrint.add_argument('-printn',"-pn",action='store_true',help=showArg("Don't print anything or allow use of the 'input' command.",argsIO))

    ParserGraph = parser.add_argument_group('Graph options')
    ParserGraph.add_argument('-graph','-g',action='store_true',help=showArg("Make a graph of the results. Uses graphviz graph-to-pdf converter",argsCommon or argsGraph))
    ParserGraph.add_argument('-graphNoSingleton','-gns',action='store_true',help=showArg("Eliminate any node with a single parent and single child.",argsGraph))
    ParserGraph.add_argument('-graphBubbles','-gb',action='store_true',help=showArg("Use circles instead, which are sized based on their odds of occuring.",argsGraph))
    ParserGraph.add_argument('-graphNoShowFile','-gnf',action='store_true',help=showArg("Don't open the PDF viewer when it finishes.",argsGraph))

    if argsGraph: ParserGraphLabels = parser.add_argument_group('Graph label options')
    else: ParserGraphLabels = ParserGraph
    ParserGraphLabels.add_argument('-graphNoLabelNodes','-gnln',action='store_true',help=showArg("Don't show node labels",argsGraph))
    ParserGraphLabels.add_argument('-graphNoLabelEdges','-gnle',action='store_true',help=showArg("Don't show edge labels",argsGraph))
    ParserGraphLabels.add_argument('-graphNoLabels','-gnl',action='store_true',help=showArg("Don't show edge or node labels. Speeds up rendering substantially.",argsGraph or argsCommon))

    if argsGraph: ParserGraphColors = parser.add_argument_group('Graph color options')
    else: ParserGraphColors = ParserGraph
    ParserGraphColors.add_argument('-graphBrightRed','-gbr',action='store_true',help=showArg("Use bright red instead of red.",argsGraph))
    ParserGraphColors.add_argument('-graphBrightGreen','-gbg',action='store_true',help=showArg("Use bright green instead of green.",argsGraph))
    ParserGraphColors.add_argument('-graphBrightBlue','-gbb',action='store_true',help=showArg("Use bright blue instead of blue.",argsGraph))
    ParserGraphColors.add_argument('-graphDarkGrey','-gdg',action='store_true',help=showArg("Use dark grey instead of grey.",argsGraph))
    ParserGraphColors.add_argument('-graphVibrant','-gv',action='store_true',help=showArg("Shorthand for all the bright/dark colors, colored borders, and colored edges. Speeds up rendering substantially.",argsCommon or argsGraph))
    ParserGraphColors.add_argument('-graphColorEdges','-gce',action='store_true',help=showArg("Color each edge the same as the node underneath.",argsGraph))
    ParserGraphColors.add_argument('-graphColorEdgesDark','-gced',action='store_true',help=showArg("Color each edge, using the dark version of the color of the node it points to.",argsGraph))
    ParserGraphColors.add_argument('-graphColorBorders','-gcb',action='store_true',help=showArg("Color the perimeter of each node the same as the rest of the node. Speeds up rendering moderately.",argsGraph))

    ParserGraphMarks = parser.add_argument_group("Graph marking options (manually customize with '! <expr>' command inside program)")
    ParserGraphMarks.add_argument('-graphAutoMark','-gm',action='store_true',help=showArg("Automatically put nodes after each 'select' or 'input'. Automatically enabled if there are no mark commands ('! <expr>') in the program.",argsGraph))
    ParserGraphMarks.add_argument('-graphAutoMarkSimple','-gms',action='store_true',help=showArg("Same as -graphAutoMark, but it leaves off the variable names from the label.",argsGraph))

    ParserGraphDebug = parser.add_argument_group("Graph debug options")
    ParserGraphDebug.add_argument('-graphProgress','-gp','-gd',action='store_true',help=showArg("Show the steps of making the graph.",argsGraph))
    ParserGraphDebug.add_argument('-graphShowErrors','-gse',action='store_true',help=showArg("Don't suppress output/errors from graphviz (the graph-to-pdf converter) and the PDF viewer",argsGraph))


    parserExtraDisp = parser.add_argument_group('Additional display options')
    parserExtraDisp.add_argument('-silent','-s',action='store_true',help=showArg("Don't warn about converting 'done' cases to 'fail' or 'pass'. Also doesn't show 'no result' message.",argsCommon or argsIO))
    parserExtraDisp.add_argument('-noAgg','-na',action='store_true',help=showArg("Don't aggregate printc statements. Don't display odds for printa and printr statements",argsIO))
    parserExtraDisp.add_argument('-intAllowed','-i',action='store_true',help=showArg("Fractions will be displayed as integers whenever possible. (For example, 3 instead of 3/1)",argsCommon or argsIO))
    parserExtraDisp.add_argument('-NoColor','-nc',action='store_true',help=showArg("Don't include ANSI color codes in printouts.",argsIO))
    parserExtraDisp.add_argument('-isatty','-tty',action='store_true',help=showArg("Assume the input and output are terminals. This may resolve issues with displaying color.",argsIO))
    parserExtraDisp.add_argument('-noGreyFill','-ng',action='store_true',help=showArg("When getting input: if the input has already been obtained, then don't display it in grey.",argsIO))
    parserExtraDisp.add_argument('-skipInp','-ni',action='store_true',help=showArg("When getting input: if the input has already been obtained, then don't display the question or answer at all.",argsIO))

    parserDebug = parser.add_argument_group('Debug options')
    parserDebug.add_argument('-DebugNoDiscards','-nd', action="store_true",help=showArg("Variables will be kept even after they are no longer needed. If the graph is merging nodes, this may prevent it.",argsCommon or   argsDebug))
    parserDebug.add_argument('-DebugStaticAnalysis','-dsa', action="store_true",help=showArg("Show a debug of the program in various stages of static analysis.",argsDebug))
    parserDebug.add_argument('-DebugDiscards','-dd', action="store_true",help=showArg("Show a debug of the discards of the program",argsDebug))
    parserDebug.add_argument('-DebugReconstruct','-dr', action="store_true",help=showArg("Display the original program, as interpreted by the parser.",argsCommon or argsDebug))
    parserDebug.add_argument('-DebugAST','-da', action="store_true",help=showArg("Display the Raw AST",argsDebug))
    args = parser.parse_args(argList)

    if args.H or args.ho or args.hg or args.hd:
        parser.print_help()
        exit()

    # Set default for args.f if all options are omitted.
    if not (args.p or args.P != None or args.d or args.D != None or args.f or args.F != None or args.b or args.B != None):
        args.f = True

    if noFileNeeded and args.file == None:
        fileS = None
    else:
        if args.file == None:
            error("Argument required: filename")

        try:
            with open(args.file,"rt",newline='') as file: fileS = file.read()
        except:
            error("Error: File could not be opened.")
    return args,fileS
