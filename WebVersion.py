from nicegui import ui
import graphviz
import asyncio
import main
import traceback
from parser import ExitException

# Note: this file started out as an AI-generated template.
# I manually changed it afterward.


def make_graph(source: str) -> str:
    """
    Take source code and return a Graphviz SVG."""
    try:
        res, graph = main.runInternal(source,"")
    except ExitException as e:
        return e.customMessage
    except Exception as e:
        e = traceback.format_exc()
        return f"""
        <pre style="
            color: #c00;
            padding: 1em;
            white-space: pre-wrap;
        ">{e}</pre>
        """

    return graph


# ------------------------------------------------------------
# GUI state
# ------------------------------------------------------------

graph = None
update_task = None


async def update_graph():
    """Regenerate the graph after the user stops typing."""

    global update_task

    source = editor.value

    svg = await asyncio.to_thread(make_graph, source)
    if svg != None: graph.content = svg



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
select a from 1 to 3
if a == 3
\tpass
fail
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
            "hello world"
        ).classes(
            'w-full flex-grow overflow-auto'
        )

ui.run()
