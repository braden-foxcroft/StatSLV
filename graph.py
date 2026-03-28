

from parser import error
from fractions import Fraction
from collections import defaultdict

def doImports():
	global graphviz
	global Digraph
	# Try importing Graphviz
	try:
		import graphviz
	except ImportError:
		error("Python package 'graphviz' is not installed. Install it with:\n\tpip install graphviz\n(You will also need to install the graphviz executable, if you haven't done so already)")

	# Do a dry run to confirm that graphviz works.
	from graphviz import Digraph
	from graphviz.backend import ExecutableNotFound
	try:
		dot = Digraph()
		dot.edge("A", "B")
		dot.pipe(format="png")
	except ExecutableNotFound:
		error(f"Graphviz executable 'dot' not found in PATH. On Linux, install it with:\n\tsudo apt install graphviz\nFor Windows, download it from the website: \n\thttps://graphviz.org/download/\n(Use the EXE installer, and make sure you ask the installer to add it to the PATH! You may need to close and re-open the console for it to take effect.)")
	except Exception as e:
		error(f"Unknown Graphviz error: {e}")

# ----------------------------------------
# End of imports


class Node:
	"""This class tracks nodes in a graph"""
	nextFree = 0
	def __init__(this,theId=None,label=None,odds=None):
		if theId == None:
			this.id = f"~{Node.nextFree}~"
			Node.nextFree += 1
		else:
			this.id = theId
		this.label = label
		this.odds = odds
		this.win = None
		this._parents = set()
		this._children = defaultdict(Fraction)

	def raw(this):
		"""The raw data"""
		res = f"id = {this.id}"
		if this.label != None:
			res += "\nlabel = {this.label}"
		if this.odds != None:
			res += "\nodds = {this.odds}"
		if this.win != None:
			res += "\nwin = {this.win}"
		if this._parents:
			res += "\nparents = {this._parents}"
		if this._children:
			res += "\nchildren = {this._children}"
		print(res)

	def __iter__(this): return iter(this._children)
	def __len__(this): return len(this._children)
	def __getitem__(this,child): return this._children[child]

	def __str__(this): return f"Node '{this.id}'"

	def __repr__(this): return f"Node '{this.id}'"

	def show(this):
		"""Show the graph"""
		print(f"{str(this)}\n" + this._toString(set()))

	def _toString(this,prevs):
		if this in prevs:
			return f"Error: {this} repeated"
		prevs.add(this)
		res = ""
		for other in this:
			res += f"{this.id} -> {other.id}\n"
		for other in this:
			res += other._toString(prevs)
		return res

	def link(this,other,odds):
		"""Add a link. Parent.link(child,odds)"""
		this._children[other] += odds
		other._parents.add(this)

	def __sub__(this,other):
		"""Remove a link.
		parent - child"""
		other._parents.remove(this)
		del this._children[other]
		return this


class Graph:
	"""A full graph. A list of nodes and their configurations."""

	def __init__(this,dummy=False):
		this.root = Node(None,"",Fraction(1,1))
		this.nodes = dict()
		this.nodes["root"] = this.root
		this.dummy = dummy # if dummy, then don't do anything.

	def __getitem__(this,theId):
		return this.nodes[theId]

	def __iter__(this):
		return iter(this.nodes)

	def newNode(this,label,odds):
		"""
		Adds a node.
		
		Takes:
		str label
		Fraction odds
		
		Returns a str node id
		"""
		if this.dummy: return "root"

		n = Node(None,label,odds)
		this.nodes[n.id] = n
		return n.id


	def addEdge(this,sourceId,destId,odds):
		"""Adds an edge. Takes str ids"""
		if this.dummy: return
		this[sourceId].link(this[destId],odds)


	def nodePass(this,theId):
		"""Marks a node as pass"""
		if this.dummy: return
		node = this[theId]
		if node.win == -1 or node.win == 0:
			node.win = 0
		if node.win == 1 or node.win == None:
			node.win = 1
	def nodeFail(this,theId):
		"""Marks a node as fail"""
		if this.dummy: return
		node = this[theId]
		if node.win == 1 or node.win == 0:
			node.win = 0
		if node.win == -1 or node.win == None:
			node.win = -1
	def nodeDone(this,theId):
		"""Marks a node as done or returned"""
		if this.dummy: return
		this[theId].win = 0
	
	def removeAllLinear(this):
		"""Remove any node with 1 parent and 1 child"""
		if this.dummy: return
		toDel = []
		for nodeId in this:
			node = this[nodeId]
			# Skip if not linear
			if len(node._parents) != 1 or len(node._children) != 1: continue
			# Remove linear node.
			parent = list(node._parents)[0]
			child = list(node._children)[0]
			parent - node
			node - child
			parent > child
			toDel.append(nodeId)
		for nodeId in toDel:
			del this.nodes[nodeId]

	def cleanup(this,node=None):
		"""Determines pass/fail for each node"""
		if this.dummy: return
		# Use root if not specified
		if node == None: node = this.root
		if node.win != None: return
		if len(node) == 0:
			node.win = 0
			return
		for child in node:
			this.cleanup(child)
		willPass = True
		willFail = True
		for child in node:
			if child.win !=  1: willPass = False
			if child.win != -1: willFail = False
		if willPass:
			node.win = 1
		elif willFail:
			node.win = -1
		else:
			node.win = 0
		return

	def convert(this,labelNodes=True,labelEdges=True,brightRed=False,brightGreen=False,brightBlue=False,removeLinear=False,useCircle=False,colorEdges=False,showPrints=True,file="output"):
		"""Generate, save, and display a graph PDF. All items are bool except 'file', which is a str."""
		if this.dummy: return print("why is 'convert' being called on a dummy graph?")
		if removeLinear:
			if showPrints: print("Removing linear nodes...",end="",flush=True)
			this.removeAllLinear() # get rid of linear nodes if needed.
			if showPrints: print("Done.")
		if showPrints: print("Choosing node colors...",end="",flush=True)
		this.cleanup() # figure out all necessary win/lose.
		if showPrints: print("Done.")
		if showPrints: print("Loading graph info...",end="",flush=True)
		dot = create_graph(useCircle)
		for nodeId in this:
			node = this[nodeId]
			add_node(dot,node.id,node.label,chooseColor(node.win,brightRed,brightGreen,brightBlue))
		for nodeId in this:
			node = this[nodeId]
			for other in node:
				label = None
				color = "black"
				if labelEdges:
					labelFrac = node[other]
					if labelFrac != 1: label = str(labelFrac)
				if colorEdges:
					if other.win == 1: color = "green"
					if other.win == -1: color = "red"
				add_edge(dot, node.id, other.id, label, color)
		if showPrints: print("Done.")
		if showPrints: print("Graphviz working...",end="",flush=True)
		toFile(dot)
		if showPrints: print("Done.")

def chooseColor(win,brightRed,brightGreen,brightBlue):
	"""win: -1 or 0 or 1, bright*: bool.
	Returns a color str"""
	if win == -1:
		if brightRed: return "red"
		return "pink"
	if win == 0:
		if brightBlue: return "blue"
		return "lightblue"
	if win == 1:
		if brightGreen: return "green"
		return "lightgreen"


def create_graph(circle=False):
	"""Creates a dot object. Takes a bool (circle or not)"""
	if circle: shape = "circle"
	else: shape = "oval"
	dot = Digraph(name="mygraph",format="pdf")
	dot.attr(rankdir="TB")
	dot.attr("node", shape=shape, style="filled")
	return dot


def add_node(dot, node_id, label=None, color="lightgray"):
	"""Takes:
	dot
	str node_id
	str label
	str color
	"""
	if label == None: label = node_id
	dot.node(node_id, label=label, fillcolor=color)


def add_edge(dot, from_id, to_id, label=None, color="black"):
	"""Takes:
	dot
	str from_id
	str to_id
	str label
	str color
	"""
	if label:
		dot.edge(from_id, to_id, label=label, color=color)
	else:
		dot.edge(from_id, to_id, color=color)


def toFile(dot,file="output"):
	"""Converts the dot object to a file."""
	dot.render(file, cleanup=True, view=True)

