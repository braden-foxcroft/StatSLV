#! /usr/bin/python3

# Note: this file started out as an AI-generated template.
# I manually changed it afterward.
# Most of the UI code is AI-generated, though.

import sys
import argumentHandling
# Argument handling at the top. This way, the '-h' flag runs faster.
args,fileS = argumentHandling.parseArgs(sys.argv[1:],True)
args.printn = True # Block print statements.
args.graph = True # make graph.

import graph
graph.doImports() # Make sure that graphviz works. Exit otherwise.

try:
    from nicegui import ui
except:
    print("Missing module 'nicegui'. To install:\n\tpip install nicegui")
    exit(1)

from time import sleep
import asyncio
import main
import traceback
from parser import ExitException
import codeEditor # The module which manages code editing.
import settingsPage


if fileS != None: # Use file contents if provided.
    codeEditor.initial_text = fileS

emptySVG = main.runInternal("return",args)[1]

graph_lock = asyncio.Lock() # The lock to ensure single-threaded graph updates.


def create_run_button(on_clicked):
    """Takes a function to call when the button is clicked,
    returns the function which sets the button mode."""


    # Create a container that positions the button at the top-right.
    button = ui.button(
        'Run',
        icon='play_arrow',
        on_click=on_clicked,
    ).props('no-caps').props('flat dense').classes('ml-auto')

    def set_run_button(mode: str):
        if mode == 'run':
            button.props('color=positive')
            button.props('icon=play_arrow')
            button.text = 'Run'
        elif mode == 'running':
            button.props('color=primary')
            button.props('icon=sync')
            button.text = 'Running'
        elif mode == 'waiting':
            button.props('color=warning')
            button.props('icon=schedule')
            button.text = 'Waiting'
        elif mode == 'timed_out':
            button.props('color=negative')
            # button.props('icon=warning')
            button.props('icon=play_arrow')
            button.text = 'Timed Out'
        elif mode == 'graph_generating':
            button.props('color=deep-purple')
            button.props('icon=device_hub')
            button.text = 'Graph Generating'
        else:
            raise ValueError(f'Unknown button mode: {mode}')

    return set_run_button


@ui.page("/")
def main_page():

    big_operation_lock = asyncio.Lock()

    # The graph obj.
    graph = None
    # Whether the settings say to auto-refresh.
    autoRefresh = True
    # Whether the settings require a manual refresh after a timeout
    autoRefreshAfterTimeout = False
    # Whether the last run timed out
    timedOut = False

    def make_graph(source: str, isManual=False) -> str:
        """
        Take source code, return a str result and a Graphviz SVG.
        Either or both return values can be None."""
        try:
            currentArgs = settingsPage.settingsToArgs(settings.get_state(),isManual)
        except:
            # This will trigger if the settings haven't been set up yet.
            currentArgs = args # The args parsed by the command-line
        try:
            res, graphVal = main.runInternal(source,currentArgs)
        except ExitException as e:
            return e.customMessage, None, False
        except main.TimerException:
            return "Timed out", None, True
        except Exception: # This isn't normally supposed to happen.
            errorTrace = traceback.format_exc()
            return errorTrace, None, False
        
        return res, graphVal, False


    async def update_graph(source,isManual=False):
        """Run the code and update the graph."""
        nonlocal timedOut
        
        set_run_button('waiting')
        async with graph_lock:
            set_run_button('running')
            resText,svgVal,timedOutFlag = await asyncio.to_thread(make_graph, source,isManual)

        if timedOutFlag:
            set_run_button('timed_out')
            timedOut = True
            return
        timedOut = False

        if resText != None: set_message(resText,svgVal == None) # Empty text is fine.

        try:
            if svgVal == None or svgVal == "No graph requested.":
                return # Don't modify the graph if there was an error or no graph was provided.

            set_run_button('graph_generating')
            with editor:
                await ui.run_javascript('''
                        if (window.graphViewer && !window.graphFitted) {
                            window.graphZoom = graphViewer.getZoom();
                            window.graphPan = graphViewer.getPan();
                            document.querySelector('#graph-container').style.visibility = 'hidden';
                        }
                    ''',timeout=5)
                
                
                if len(svgVal) > 2000000:
                    # the viewer will never finish being made.
                    graph.content="Graph is too big to display on the website. Use the command-line interface to make large graphs instead. Turning off labels may help as well."
                    
                    await ui.run_javascript("""
                        window.graphViewer = false;
                        document.querySelector('#graph-container').style.visibility = 'visible';""")
                    return

                async with big_operation_lock:
                    graph.content = svgVal

                    await asyncio.sleep(0.1)
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
                    ''',timeout=20)
        finally:
            set_run_button('run')

    # ------------------------------------------------------------
    # Graph worker threading.
    # ------------------------------------------------------------

    # Used by the graph worker, which completes tasks one-by-one.
    pending_code = None
    pending_code_is_autorun = False
    worker_task = None

    async def worker():
        nonlocal pending_code, pending_code_is_autorun

        while True:
            # Take the latest pending version.
            source = pending_code
            pending_code = None
            is_autorun = pending_code_is_autorun
            pending_code_is_autorun = False
            if source is None: break # No code waiting.

            if is_autorun and (not autoRefresh or (timedOut and not autoRefreshAfterTimeout)):
                continue # Skip if it is an invalid auto-refresh.
            # Generate the graph without blocking the event loop.
            await update_graph(source, not is_autorun)


    def request_update(e,manual_run=False):
        nonlocal pending_code, worker_task,pending_code_is_autorun
        # Get the actual code and tell it to be the next run.
        if isinstance(e,str):
            source = str(e)
        else:
            source = e.args["text"]

        pending_code = source
        pending_code_is_autorun = not manual_run

        # Start a worker if one isn't already running.
        if worker_task is None or worker_task.done():
            worker_task = asyncio.create_task(worker())

    # ------------------------------------------------------------
    # Page layout
    # ------------------------------------------------------------


    ui.page_title('StatSLV')

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
            results_panel.set_visibility(True)
            title.text = 'Source Code'
            toggle_button.props('icon=settings')
        else:
            settings_panel.set_visibility(True)
            editor_panel.set_visibility(False)
            results_panel.set_visibility(False)
            title.text = 'Settings'
            toggle_button.props('icon=code')

    leftShown = True
    rightShown = True
    def showColumn(left=True,right=True):
        nonlocal leftShown,rightShown
        leftShown,rightShown = left,right
        if left and not right:
            leftCol.classes(remove="w-1/2 hidden",
                add="w-full")
            rightCol.classes(remove="w-1/2 w-full",
                add="hidden")
        elif right and not left:
            rightCol.classes(remove="w-1/2 hidden",
                add="w-full")
            leftCol.classes(remove="w-1/2 w-full",
                add="hidden")
        else:
            leftCol.classes(remove="w-full hidden",
                add="w-1/2")
            rightCol.classes(remove="w-full hidden",
                add="w-1/2")

    def bigGraphToggle(e):
        if leftShown:
            showColumn(False,True)
            graph_toggle_button.icon = "fullscreen_exit"
        else:
            showColumn(True,True)
            graph_toggle_button.icon = "fullscreen"


    async def settings_changed():
        nonlocal autoRefresh,autoRefreshAfterTimeout
        with settings_panel:
            state = settings.get_state()
            autoRefresh = state.auto_refresh
            autoRefreshAfterTimeout = not state.require_manual_refresh
            if state.graph:
                showColumn()
            else:
                showColumn(True,False)
            timer_val = state.debounce_timer
            try: timer_val = int(timer_val)
            except: timer_val = 0
            if timer_val < 0: timer_val = -timer_val # abs value
            await ui.run_javascript(f'window.debounceTimeout = {timer_val}')
            code = await ui.run_javascript('window.codeEditor.state.doc.toString()')
            request_update(code) # Updates the graph when it gets the chance.

    def set_message(text: str, error: bool = False):
        with results_panel:
            if not text:
                results_panel.set_text('')
                results_panel.style('display: none;')
                return

            if error: color = '#FF5555' # red
            else: color = 'white'
            
            font_size = '1.1rem' if not error else '0.875rem'
            
            
            results_panel.set_text(text)
            results_panel.style(
                f'display: block; color: {color}; font-size: {font_size};'
            )

    async def request_update_manual(e):
        code = await ui.run_javascript('window.codeEditor.state.doc.toString()')
        # Request manual update when it gets the chance.
        request_update(code,True)

    with ui.row().classes('w-full h-screen no-wrap'):

        # Left side: editor
        with ui.column().classes('w-1/2 h-full pt-3') as leftCol:

            with ui.row().classes('w-full items-center px-2'):
                title = ui.label('Source Code').classes('text-lg font-bold p-2')

                set_run_button = create_run_button(request_update_manual)
                toggle_button = ui.button(
                    icon='settings'
                ).props('flat round dense')

            with ui.element('div').classes(
                'w-full flex-1 min-h-0 overflow-auto'
            ) as editor_panel:
                editor = codeEditor.makeEditor()

            with ui.element('div').classes(
                'w-full flex-grow overflow-auto'
            ) as settings_panel:
                settings = settingsPage.Settings(on_change=settings_changed)

            results_panel = ui.label().classes(
                'w-full whitespace-pre-wrap break-words rounded p-2 shrink-0 font-mono bg-black dark:bg-gray-200 mb-2'
            )


            settings_panel.set_visibility(False)
            settings.set_state(settingsPage.argsToSettings(args))

            toggle_button.on_click(toggle_settings)

        
        ui.on('code_changed', request_update)

        # Right side: graph
        with ui.column().classes('w-1/2 h-98/100 pt-3') as rightCol:

            with ui.row().classes('w-full items-center px-2'):
                ui.label('Graph').classes(
                    'text-lg font-bold p-2'
                )

                graph_toggle_button = ui.button(
                    icon='fullscreen',
                    on_click=bigGraphToggle
                ).props('flat round dense').classes('ml-auto')

            with ui.element('div').classes('relative w-full h-full overflow-hidden'):
                
                graph = ui.html(
                    emptySVG
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
        ''',timeout=120.0)


    async def firstPass():
        """Makes a trivial SVG, configures the svg viewer, configures the editor, then replaces the SVG with the right one."""
        with editor:
            await makeSVGViewer()
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
                    if (graphViewer) {
                        graphViewer.fit();
                        graphViewer.center();
                    }
                    window.fitButton.style.display = 'none';
                    window.graphFitted = true;
                };

                fitButton.addEventListener('press',fitGraph);

                fitGraph()
                makeEditor()
            ''')
            request_update(codeEditor.initial_text)

    ui.timer(0.2,firstPass,once=True)

ui.run(reload=False)
