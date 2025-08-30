

from parser import parse
from staticAnalysis import deAlias,addMetadata
import argparse

parser = argparse.ArgumentParser(description="An interpreter for the StatSLV programming language.")
parser.add_argument('file', action="store",help="The file to run.")
parser.add_argument('--noDiscards', action="store_true",help="Don't discard variables automatically when they are no longer needed.")
parser.add_argument('--reconstruct', action="store_true",help="Display the original program, as interpreted by the parser.")
parser.add_argument('-p',action='store',help="Display the result as a percentage rounded to 'P' decimal places")
parser.add_argument('-f',action='store',help="If '-p' is present, also print the fraction result.")
parser.add_argument('-silent',action='store_true',help="Don't warn about converting cases to fail or pass.")
args = parser.parse_args()
print(args)


# with open("parser.py","rt",newline='') as file: s = file.read()