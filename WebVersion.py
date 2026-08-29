from nicegui import ui
import graphviz
import asyncio


# Note: this file started out as an AI-generated template.
# I manually changed it afterward.


# ------------------------------------------------------------
# Your existing analyzer goes here
# ------------------------------------------------------------

def make_graph(source: str) -> str:
    """
    Take source code and return a Graphviz SVG.

    Replace this function with your actual analyzer.
    """

    dot = graphviz.Digraph(format='svg')

    # Example graph just to demonstrate the GUI
    dot.node('A', source)
    dot.node('B', 'Parser')
    dot.node('C', 'Analyzer')
    dot.node('D', 'Output')

    dot.edge('A', 'B')
    dot.edge('B', 'C')
    dot.edge('C', 'D')

    return dot.pipe().decode('utf-8')


# ------------------------------------------------------------
# GUI state
# ------------------------------------------------------------

graph = None
update_task = None


async def update_graph():
    """Regenerate the graph after the user stops typing."""

    global update_task

    source = editor.value

    try:
        svg = await asyncio.to_thread(make_graph, source)

        graph.content = svg

    except Exception as e:
        graph.content = f"""
        <pre style="
            color: #c00;
            padding: 1em;
            white-space: pre-wrap;
        ">{e}</pre>
        """


# ------------------------------------------------------------
# Page layout
# ------------------------------------------------------------

ui.page_title('Code Graph Explorer')

with ui.row().classes('w-full h-screen no-wrap'):

    # Left side: editor
    with ui.column().classes('w-1/2 h-full'):

        ui.label('Source Code').classes(
            'text-lg font-bold p-2'
        )

        editor = ui.textarea(
            value='''\
foo = 1
bar = foo + 2
baz = bar * 3
'''
        ).classes(
            'w-full flex-grow font-mono'
        )

        editor.on_value_change(update_graph)

    # Right side: graph
    with ui.column().classes('w-1/2 h-full'):

        ui.label('Graph').classes(
            'text-lg font-bold p-2'
        )

        graph = ui.html(
            make_graph(editor.value)
        ).classes(
            'w-full flex-grow overflow-auto'
        )


ui.run()
