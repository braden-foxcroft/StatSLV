#! /usr/bin/python3

# Note: this file started out as an AI-generated template.
# I manually changed it afterward.
# Most of the UI code is AI-generated, though.

from time import sleep
import sys
import argumentHandling
# Argument handling. This way, the '-h' flag runs faster.
args,fileS = argumentHandling.parseArgs(sys.argv[1:],True)
args.printn = True # Block print statements.

import graph
graph.doImports() # Make sure that graphviz works. Exit otherwise.

try:
    from nicegui import ui
except:
    print("Missing module 'nicegui'. To install:\n\tpip install nicegui")
    exit(1)

import asyncio
import main
import traceback
from parser import ExitException
import codeEditor # The module which manages code editing.
import settingsPage




if fileS != None: # Use file contents if provided.
    codeEditor.initial_text = fileS

def make_graph(source: str) -> str:
    """
    Take source code and return a Graphviz SVG."""
    try:
        currentArgs = settingsPage.settingsToArgs(settings.get_state())
    except:
        # This will trigger if the settings haven't been set up yet.
        currentArgs = args # The args parsed by the command-line
    try:
        res, graph = main.runInternal(source,currentArgs)
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

async def update_graph(e):
    """Regenerate the graph after the user stops typing."""

    if isinstance(e,str):
        source = str(e)
    else:
        source = e.args["text"]

    svgVal = await asyncio.to_thread(make_graph, source)
    if svgVal == None: return
    await ui.run_javascript('''
            if (window.graphViewer && !window.graphFitted) {
                window.graphZoom = graphViewer.getZoom();
                window.graphPan = graphViewer.getPan();
                document.querySelector('#graph-container').style.visibility = 'hidden';
            }
        ''')
    
    graph.content = svgVal

    await makeSVGViewer()

    await ui.run_javascript('''
        if (window.graphFitted) {
            graphFitted = false
            graphViewer.updateBBox();
            fitGraph()
        } else if (window.graphViewer) {
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

    .nicegui-content {
        padding-top: 0px;
        padding-bottom: 0px;
        box-sizing: border-box;
    }

    #code-editor {
    width: 100%;
    height: 100%;
}

    #code-editor .cm-editor {
        height: 100% !important;
    }

    #code-editor .cm-scroller {
        overflow: auto !important;
    }
''')

def toggle_settings():
    if settings_panel.visible:
        settings_panel.set_visibility(False)
        editor_panel.set_visibility(True)
        title.text = 'Source Code'
        toggle_button.props('icon=settings')
    else:
        editor_panel.set_visibility(False)
        settings_panel.set_visibility(True)
        title.text = 'Settings'
        toggle_button.props('icon=code')

async def settings_changed(state):
    with settings_panel:
        code = await ui.run_javascript('window.codeEditor.state.doc.toString()')
        if code != "":
            await update_graph(code) # Updates the graph immediately.


with ui.row().classes('w-full h-screen no-wrap'):

    # Left side: editor
    with ui.column().classes('w-1/2 h-full pt-3'):

        with ui.row().classes('w-full items-center px-2'):
            title = ui.label('Source Code').classes('text-lg font-bold')

            toggle_button = ui.button(
                icon='settings'
            ).props('flat round dense').classes('ml-auto')

        with ui.element('div').classes(
            'w-full flex-grow overflow-hidden'
        ) as editor_panel:
            editor = codeEditor.makeEditor()

        with ui.element('div').classes(
            'w-full flex-grow overflow-auto'
        ) as settings_panel:
            settings = settingsPage.Settings(on_change=settings_changed)

        settings_panel.set_visibility(False)
        settings.set_state(settingsPage.argsToSettings(args))

        toggle_button.on_click(toggle_settings)

    
    ui.on('code_changed', update_graph)

    # Right side: graph
    with ui.column().classes('w-1/2 h-98/100 pt-3'):

        ui.label('Graph').classes(
            'text-lg font-bold p-2'
        )

        with ui.element('div').classes('relative w-full h-full overflow-hidden'):
            
            # TODO make_graph can fail.
            graph = ui.html(
                make_graph(codeEditor.initial_text)
            ).props(
                'id=graph-container'
            ).classes(
                'w-full h-full border border-black'
            )

            ui.button(
                icon='fit_screen',
                on_click=lambda: ui.run_javascript('fitGraph()')
            ).props(
                'flat round dense id="fullsize-button"'
            ).classes(
                'absolute top-1 right-1 z-10'
            ).tooltip('Keep full graph visible')

 
# Make the code editor
codeEditor.addEditorScript()

alreadyRunOnce = False
async def makeSVGViewer():
    global alreadyRunOnce
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

            graphViewer.setOnPan(() => {
                if (graphFitted) {
                    graphFitted = false;
                    fitButton.style.display = '';
                }
            });

            graphViewer.setOnZoom(() => {
                if (graphFitted) {
                    graphFitted = false;
                    fitButton.style.display = '';
                }
            });
        }
    ''')
    if not alreadyRunOnce:
        await ui.run_javascript('''
window.fitButton = document.querySelector('#fullsize-button');
window.graphFitted = false;
const observer = new ResizeObserver(() => {
    graphViewer.resize();
    if (graphFitted) {
        fitGraph()
    }
});

observer.observe(document.getElementById('graph-container'));

window.fitGraph = function() {
    window.graphFitted = false;
    graphViewer.fit();
    graphViewer.center();
    window.fitButton.style.display = 'none';
    window.graphFitted = true;
};

fitButton.addEventListener('press',fitGraph);

fitGraph()
makeEditor()
        ''')
        alreadyRunOnce = True


ui.timer(0.1, makeSVGViewer, once=True)

ui.run(reload=False)
