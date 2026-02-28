

from parser import error
from fractions import Fraction

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
			theId = f"~{nextFree}~"
			nextFree += 1
		else:
			this.id = theId
		this.label = label
		this.odds = odds
		this.color = None
		this._parents = set()
		this._children = set()

	def raw(this):
		"""The raw data"""
		res = f"id = {this.id}"
		if this.label != None:
			res += "\nlabel = {this.label}"
		if this.odds != None:
			res += "\nodds = {this.odds}"
		if this.color != None:
			res += "\ncolor = {this.color}"
		if this._parents:
			res += "\nparents = {this._parents}"
		if this._children:
			res += "\nchildren = {this._children}"
		print(res)

	def __iter__(this): return iter(this._children)
	def __len__(this): return len(this._children)

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


	def __lt__(this,other):
		"""Add a link"""
		other._children.add(this)
		this._parents.add(other)
		return other

	def __sub__(this,other):
		"""Remove a link made with '>'"""
		other._parents.remove(this)
		this._children.remove(other)
		return this


class Graph:
	"""A full graph. A list of nodes and their configurations."""

	def __init__(this):
		this.root = Node(None,"",Fraction(1,1))
		this.nodes = set()
		this.nodes.add(this.root)

	# TODO function for adding nodes
	# TODO function for linking nodes
	# TODO function for marking as pass/fail.
	# TODO function for removing a -> b -> c where b is singular.
	# TODO function for final cleanup: propagating pass/fail


# ----------------------------------------------------
# TODO this is AI-generated


def create_graph():
    dot = Digraph(name="mygraph",format="pdf")
    dot.attr(rankdir="TB")
    dot.attr("node", shape="oval", style="filled")
    return dot


def add_node(dot, node_id, label=None, color="lightgray"):
    """
    Takes:
    str node_id
    str label
    str color
    """
    if label == None: label = node_id
    dot.node(node_id, label=label, fillcolor=color)


def add_edge(dot, from_id, to_id, label=None, color="black"):
    """
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
    dot.render(file, cleanup=True, view=True)


dot = create_graph()
add_node(dot,"a","A","pink")
add_node(dot,"b","B","lightblue")
add_node(dot,"b2","BB","lightblue")
add_node(dot,"c","C","lightgreen")

add_edge(dot,"a","b","1/2","green")
add_edge(dot,"a","b2","1/3","red")
add_edge(dot,"b","c")
add_edge(dot,"b2","c")

toFile(dot)

