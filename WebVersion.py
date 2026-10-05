try:
    from nicegui import ui
except:
    print("Missing module 'nicegui'. To install:\n\tpip install nicegui")
    exit(1)

import graphviz
import asyncio
import main
import traceback
from parser import ExitException
import graph

graph.doImports() # Make sure that the imports work.

# Note: this file started out as an AI-generated template.
# I manually changed it afterward.


def make_graph(source: str) -> str:
    """
    Take source code and return a Graphviz SVG."""
    try:
        res, graph = main.runInternal(source,"")
    except ExitException as e:
        return None # TODO errors unhandled
        return e.customMessage
    except Exception as e:
        return None # TODO errors unhandled
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


async def update_graph():
    """Regenerate the graph after the user stops typing."""


    source = editor.value

    svgVal = await asyncio.to_thread(make_graph, source)
    if svgVal == None: return
    await ui.run_javascript('''
            if (window.graphViewer) {
                window.graphZoom = graphViewer.getZoom();
                window.graphPan = graphViewer.getPan();
                document.querySelector('#graph-container').style.visibility = 'hidden';
            }
        ''')

    graph.content = svgVal

    await makeSVGViewer()

    await ui.run_javascript('''
        if (window.graphViewer) {
            graphViewer.updateBBox();

            if (window.graphZoom !== undefined) {
                graphViewer.zoom(graphZoom);
                graphViewer.pan(graphPan);
            }
                document.querySelector('#graph-container').style.visibility = 'visible';
        }
    ''')



# ------------------------------------------------------------
# Page layout
# ------------------------------------------------------------

ui.page_title('Code Graph Explorer')

ui.add_head_html('''
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
''')

ui.add_css('''
    #graph-container {
        width: 100%;
        height: 100%;
    }

    #graph-container svg {
        width: 100%;
        height: 100%;
    }
''')

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
            make_graph(editor.value)
        ).props(
            'id=graph-container'
        ).classes(
            'w-full h-full flex-grow overflow-auto'
        )



async def makeSVGViewer():
    await ui.run_javascript('''
        const svg = document.querySelector('#graph-container svg');

        if (svg) {
            window.graphViewer = svgPanZoom(svg, {
                zoomEnabled: true,
                panEnabled: true,
                mouseWheelZoomEnabled: true,
                dblClickZoomEnabled: true,
                controlIconsEnabled: false,
                fit: true,
                center: true,
            });
        }
    ''')

ui.timer(0.1, makeSVGViewer, once=True)


ui.run()
