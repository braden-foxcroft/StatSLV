from dataclasses import dataclass
from typing import Callable

from nicegui import ui
import argumentHandling
import asyncio


# Note: most of the code in this file is AI-generated.
# I modified it afterwards as-needed.

def argsToSettings(args):
    """Take args processed by argumentHandling, and return a SettingsState object.
    Since some options in SettingsState aren't controlled by the command-line args, these options will use the default values. Thus, this function should only be called when initializing settings in the first place, and then not used thereafter."""
    sets = SettingsState()
    sets.percentage = args.p or args.P != None
    sets.decimal = args.d or args.D != None
    sets.fraction = args.f or args.F != None or args.b or args.B != None
    sets.percentage_decimals = args.P
    sets.decimal_decimals = args.D
    if args.F != None:   sets.fraction_max_denominator = args.F
    elif args.B != None: sets.fraction_max_denominator = args.B
    sets.no_warnings = args.silent
    sets.display_ints = args.intAllowed

    sets.no_singleton = args.graphNoSingleton
    sets.weighted_bubbles = args.graphBubbles
    sets.node_labels = not args.graphNoLabelNodes and not args.graphNoLabels
    sets.edge_labels = not args.graphNoLabelEdges and not args.graphNoLabels

    sets.red   = args.graphBrightRed   or args.graphVibrant
    sets.green = args.graphBrightGreen or args.graphVibrant
    sets.blue  = args.graphBrightBlue  or args.graphVibrant
    sets.grey  = args.graphDarkGrey    or args.graphVibrant

    if args.graphColorEdgesDark:
        sets.color_edges = 'darker than child'
    elif args.graphColorEdges or args.graphVibrant:
        sets.color_edges = 'same as child'
    else:
        sets.color_edges = 'leave black'

    sets.borders = not args.graphColorBorders and not args.graphVibrant
    if args.graphAutoMarkSimple:
        sets.automark = 'simple'
    elif args.graphAutoMark:
        sets.automark = 'full'
    else:
        sets.automark = 'auto'

    sets.no_discards = args.DebugNoDiscards
    sets.graph = True # Make a graph automatically
    if args.timeout != None:
        sets.auto_refresh_timeout = args.timeout

    return sets

def settingsToArgs(sets,manualRun=False):
    """Take a SettingsState obj (and optionally whether it is a manual run or an auto-run, used for timeouts)
    returns args from argumentHandling."""
    args,_ = argumentHandling.parseArgs([],True) # an empty args object.
    args.f = False # Since this is on by default.

    if sets.percentage and sets.percentage_decimals == None: args.p = True
    if sets.decimal and sets.decimal_decimals == None: args.d = True
    if sets.fraction and sets.fraction_max_denominator == None: args.f = True
    args.P = sets.percentage_decimals
    args.D = sets.decimal_decimals
    args.F = sets.fraction_max_denominator

    args.silent = sets.no_warnings
    args.intAllowed = sets.display_ints

    args.graph = sets.graph
    args.graphNoSingleton = sets.no_singleton
    args.graphBubbles = sets.weighted_bubbles
    args.graphNoLabelNodes = not sets.node_labels
    args.graphNoLabelEdges = not sets.edge_labels

    args.graphBrightRed = sets.red
    args.graphBrightGreen = sets.green
    args.graphBrightBlue = sets.blue
    args.graphDarkGrey = sets.grey

    if sets.color_edges == 'darker than child':
        args.graphColorEdgesDark = True
    elif sets.color_edges == 'same as child':
        args.graphColorEdges = True

    args.graphColorBorders = not sets.borders 
    if sets.automark == 'simple':
        args.graphAutoMarkSimple = True
    elif sets.automark == 'full':
        args.graphAutoMark = True

    args.DebugNoDiscards = sets.no_discards

    if manualRun: args.timeout = sets.manual_refresh_timeout
    else: args.timeout = sets.auto_refresh_timeout

    # Bonus, to suppress printing and inputs:
    args.printn = True
    

    return args

def toIntOrNone(val: float | None):
    if val == None: return val
    return int(val)



@dataclass
class SettingsState:
    # Auto-refresh
    auto_refresh: bool = True
    auto_refresh_timeout: float = 5.0
    require_manual_refresh: bool = True
    manual_refresh_timeout: float | None = 20.0

    # Output
    percentage: bool = False
    percentage_decimals: int | None = None
    decimal: bool = False
    decimal_decimals: int | None = None
    fraction: bool = False
    fraction_max_denominator: int | None = None
    no_warnings: bool = False
    display_ints: bool = False

    # Graph
    graph: bool = True
    no_singleton: bool = False
    weighted_bubbles: bool = False
    node_labels: bool = True
    edge_labels: bool = True
    borders: bool = True

    red: bool = False
    green: bool = False
    blue: bool = False
    grey: bool = False

    color_edges: str = 'leave black'
    no_discards: bool = False
    automark: str = 'auto'

    debounce_timer: int = 500 # This isn't used by args.


class Settings:
    def __init__(self, on_change = None):
        self._on_change = on_change
        self._create_ui()
        self._updating = False

    def _create_ui(self):
        # ------------------------------------------------------------
        # Auto-refresh
        # ------------------------------------------------------------

        self._section('Auto-refresh')

        self.auto_refresh,_ = self._switch(
            'Auto-refresh',
            True,
            "Automatically refresh the graph when the code changes.\nYou can manually refresh with the run button in the top-left corner of the graph."
        )

        self.auto_refresh_timeout = self._number(
            'Auto-refresh timeout',
            5.0,
            min_value=0,
            step=0.1,
            tooltip="How many seconds before an auto-refresh gives up?\nIf it gives up, the refresh button will show that it timed out.\nTimeouts are measured for code execution only; graph generation is not timed."
        )

        self.require_manual_refresh,_ = self._switch(
            'Require manual refresh after timeout',
            True,
            tooltip="If a graph refresh times out, then auto-refresh will be temporarily disabled until a successful manual refresh."
        )

        self.manual_refresh_timeout = self._number(
            'Manual refresh timeout',
            20.0,
            min_value=0,
            step=0.1,
            clearable=True,
            tooltip="How long before a manual refresh gives up?\nIf this is left empty, it will keep running indefinitely.\nSince only 1 StatSLV program can run at a time, you may need to restart the server to stop the execution."
        )

        # ------------------------------------------------------------
        # Output
        # ------------------------------------------------------------

        self._section('Output')

        self.percentage,_ = self._switch(
            'Percentage',
            False,
            tooltip="Show the odds of a 'pass' in percentage form\nEx: 25%"
        )

        (
            self.percentage_decimals,
            self.percentage_decimals_row,
        ) = self._integer(
            'How many decimals to round to',
            None,
            tooltip="1 decimal means 33.3%.\nLeaving it blank will round based on python's automatic number display rules."
        )

        self.decimal,_ = self._switch(
            'Decimal',
            False,
            tooltip="Show the odds of a 'pass' in decimal form\nEx: 0.33"
        )

        (
            self.decimal_decimals,
            self.decimal_decimals_row,
        ) = self._integer(
            'How many decimals to round to',
            None,
            tooltip="2 decimals means 0.33.\n5 decimals means 0.33333\n"
        )

        self.fraction,self.fraction_label = self._switch(
            'Fraction',
            False,
            tooltip="Show the odds of a 'pass' in fraction form\nEx: 1/4\nIf all options are disabled, this one is the default."
        )

        (
            self.fraction_max_denominator,
            self.fraction_max_denominator_row,
        ) = self._integer(
            'Max denominator size',
            None,
            tooltip="How big should the denominator of the fraction be allowed to be?\nIf you set it to '10', then it will properly show fractions like 1/5 or 1/7,\nbut numbers like 2/11 will be rounded to 1/6 instead."
        )

        self.no_warnings,_ = self._switch(
            'No warnings',
            False,
            tooltip="Don't show messages like:\n- no result\nor\n- converted 'done' cases to 'pass'.\nIf the output box is completely empty, it will automatically hide.\nErrors will always show, though."
        )

        self.display_ints,_ = self._switch(
            'Display fractions as integers whenever possible',
            False,
            tooltip="In the output of the program, display whole-numbered fractions like '5/1' as '5' instead."
        )

        # ------------------------------------------------------------
        # Graph
        # ------------------------------------------------------------

        self._section('Graph')

        self.graph,_ = self._switch(
            'Make graph',
            True,
            tooltip="Make a graph for output."
        )

        self.no_singleton,_ = self._switch(
            'No singleton',
            False,
            tooltip="If a node has one arrow going in and one arrow going out, it will erase the node and join the arrows directly."
        )

        self.weighted_bubbles,_ = self._switch(
            'Weighted bubbles',
            False,
            tooltip="Show the nodes as circles, where the size of the circle is approximately based on the odds of it occuring."
        )

        self.borders,_ = self._switch(
            'Borders',
            True,
            tooltip="Should nodes have borders?\nIf disabled, this speeds up graph generation."
        )

        self.node_labels,_ = self._switch(
            'Node labels',
            True,
            tooltip="disable text labels on nodes (the ovals on the graph).\nThis speeds up graph generation."
        )

        self.edge_labels,_ = self._switch(
            'Edge labels',
            True,
            tooltip="disable text labels on edges (the arrows on the graph).\nThis often makes the arrows straighter, especially in complex graphs.\nThis speeds up graph generation."
        )

        self.red,_ = self._switch(
            'Bright red',
            False,
            tooltip="The color used by nodes where they are guaranteed to eventually 'fail'.\nBright or faded red"
        )

        self.green,_ = self._switch(
            'Dark green',
            False,
            tooltip="The color used by nodes where they are guaranteed to eventually 'pass'.\nDark or faded green"
        )

        self.blue,_ = self._switch(
            'Bright blue',
            False,
            tooltip="The color used by nodes which don't have a guaranteed outcome.\nBright or faded blue"
        )

        self.grey,_ = self._switch(
            'Dark grey',
            False,
            tooltip="The color used by nodes which were omitted from the odds calculation because they failed a 'bychance' check.\nLight or dark grey"
        )

        self.color_edges = self._choice(
            'Color edges',
            ['same as child', 'darker than child', 'leave black'],
            'leave black',
            tooltip="either:\n1. A red arrow points to a red node,\n2. A dark red arrow points to a red node,\n3. All arrows are black\nThis setting is good for giant graphs, since it turns zoomed-out sections into textureless colored blobs."
        )

        self.automark = self._choice(
            'Auto-marking',
            ['auto', 'full', 'simple'],
            'auto',
            tooltip="'marks' are how the interpreter decides which nodes should appear in the graph.\nUsing commands like:\n! a + b\nyou can manually configure the node labels and positions.\nAuto: if no '!' commands are included, auto-mark using 'full' mode.\nFull: after each line containing 'select', add a mark with the var name and value.\nSimple: after each line containing 'select', add a mark with the var value only."
        )

        self._section('Misc')

        self.no_discards,_ = self._switch(
            'No discards',
            False,
            tooltip="Normally, variables are set to 'None' the moment the compiler decides their value is no longer needed.\nThis often simplifies the structure of the graph.\nWhen you turn this setting on, it will keep variable values even when they aren't needed.\nThis often makes the graph bigger and less readable, but sometimes it makes graphs more readable instead.\nIf you want to discard variables manually, just use:\nvar_name = None"
        )

        (
            self.debounce_timer,
            self.debounce_timer_row,
        ) = self._integer(
            'Debounce timer (ms)',
            500,
            tooltip="How many milliseconds should the editor go without further typing before it auto-runs the code?\n0 or an empty box means 'instant'\n500 means 1/2 a second"
        )

        # self._update_dependencies()

    # ----------------------------------------------------------------
    # UI creation helpers
    # ----------------------------------------------------------------

    def _section(self, text: str):
        ui.label(text).classes(
            'w-full px-3 py-1.5 mt-3 rounded '
            'bg-gray-200 dark:bg-gray-700 '
            'text-base font-bold'
        )
    def _multiline_tooltip(self,text):
        return ui.tooltip(text).classes('whitespace-pre-line')

    def _help_button(self,tooltip):
        button = ui.button('?').props(
            'flat round dense'
        ).classes('ml-1')
        with button:
            self._multiline_tooltip(tooltip)
        # Tooltips can be added here later.
        # button.tooltip('...')

        return button

    def _switch(self, label: str, value: bool, tooltip : str):
        with ui.row().classes('w-full items-center px-3'):
            switch = ui.switch(value=value)
            label = ui.label(label).classes('flex-grow')
            self._help_button(tooltip)

        switch.on_value_change(self._changed)

        return switch,label

    def _number(
        self,
        label: str,
        value: float | None,
        min_value: float | None = None,
        step: float = 0.1,
        clearable: bool = False,
        tooltip: str = ""
    ):
        with ui.row().classes('w-full items-center px-3'):
            ui.label(label).classes('flex-grow')

            number = ui.number(
                value=value,
                min=min_value,
                step=step,
            ).classes('w-28')

            if clearable:
                number.props('clearable')

            self._help_button(tooltip)

        number.on_value_change(self._changed)

        return number

    def _integer(self, label: str, value: int | None, tooltip : str):
        with ui.row().classes('w-full items-center px-3') as row:
            ui.label(label).classes('flex-grow')

            number = ui.number(
                value=value,
                min=0,
                step=1,
            ).props('clearable').classes('w-28')

            self._help_button(tooltip)

        number.on_value_change(self._changed)

        return number, row

    def _choice(
        self,
        label: str,
        options: list[str],
        value: str,
        tooltip: str
    ):
        with ui.row().classes('w-full items-center px-3'):
            select = ui.select(
                options,
                value=value,
                label=label,
            ).classes('flex-grow')

            self._help_button(tooltip)

        select.on_value_change(self._changed)

        return select

    # ----------------------------------------------------------------
    # State handling
    # ----------------------------------------------------------------

    def get_state(self) -> SettingsState:
        return SettingsState(
            auto_refresh=self.auto_refresh.value,
            # TODO data validation on timeouts.
            auto_refresh_timeout=self.auto_refresh_timeout.value,
            require_manual_refresh=self.require_manual_refresh.value,
            manual_refresh_timeout=self.manual_refresh_timeout.value,

            percentage=self.percentage.value,
            percentage_decimals=toIntOrNone(self.percentage_decimals.value),
            decimal=self.decimal.value,
            decimal_decimals=toIntOrNone(self.decimal_decimals.value),
            fraction=self.fraction.value,
            fraction_max_denominator=toIntOrNone(self.fraction_max_denominator.value),
            no_warnings=self.no_warnings.value,
            display_ints=self.display_ints.value,

            graph=self.graph.value,
            no_singleton=self.no_singleton.value,
            weighted_bubbles=self.weighted_bubbles.value,
            node_labels=self.node_labels.value,
            edge_labels=self.edge_labels.value,

            red=self.red.value,
            green=self.green.value,
            blue=self.blue.value,
            grey=self.grey.value,

            color_edges=self.color_edges.value,
            borders=self.borders.value,
            automark=self.automark.value,
            no_discards=self.no_discards.value,
            debounce_timer=toIntOrNone(self.debounce_timer.value),
        )

    def set_state(self, state: SettingsState):
        self._updating = True

        try:
            self.auto_refresh.value = state.auto_refresh
            self.auto_refresh_timeout.value = state.auto_refresh_timeout
            self.require_manual_refresh.value = state.require_manual_refresh
            self.manual_refresh_timeout.value = state.manual_refresh_timeout

            self.percentage.value = state.percentage
            self.percentage_decimals.value = state.percentage_decimals
            self.decimal.value = state.decimal
            self.decimal_decimals.value = state.decimal_decimals
            self.fraction.value = state.fraction
            self.fraction_max_denominator.value = state.fraction_max_denominator
            self.no_warnings.value = state.no_warnings
            self.display_ints.value = state.display_ints

            self.graph.value = state.graph
            self.no_singleton.value = state.no_singleton
            self.weighted_bubbles.value = state.weighted_bubbles
            self.node_labels.value = state.node_labels
            self.edge_labels.value = state.edge_labels

            self.red.value = state.red
            self.green.value = state.green
            self.blue.value = state.blue
            self.grey.value = state.grey

            self.color_edges.value = state.color_edges
            self.borders.value = state.borders
            self.automark.value = state.automark

            self.no_discards.value = state.no_discards
            self.debounce_timer.value = state.debounce_timer

            self._update_dependencies()

        finally:
            self._updating = False

    # ----------------------------------------------------------------
    # Dependencies
    # ----------------------------------------------------------------

    def _update_dependencies(self):

        # Output precision fields only make sense when their
        # corresponding output format is enabled.
        self.percentage_decimals_row.set_visibility(
            self.percentage.value
        )

        self.decimal_decimals_row.set_visibility(
            self.decimal.value
        )

        self.fraction_max_denominator_row.set_visibility(
            self.fraction.value
        )

    # ----------------------------------------------------------------
    # Change callback
    # ----------------------------------------------------------------

    def _changed(self, _=None):
        if self._updating:
            return

        self._update_dependencies()
        if self._on_change is not None:
            asyncio.create_task(self._on_change())