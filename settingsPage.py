from dataclasses import dataclass
from typing import Callable

from nicegui import ui


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

    # Graph
    no_singleton: bool = False
    weighted_bubbles: bool = False
    node_labels: bool = True
    edge_labels: bool = True

    red: str = 'faded'
    green: str = 'faded'
    blue: str = 'faded'
    grey: str = 'light'

    color_edges: str = 'leave black'
    borders: bool = True
    automark: str = 'full'


class Settings:
    def __init__(self, on_change = None):
        self._on_change = on_change
        self._updating = False

        self._create_ui()

    def _create_ui(self):
        # ------------------------------------------------------------
        # Auto-refresh
        # ------------------------------------------------------------

        self._section('Auto-refresh')

        self.auto_refresh = self._switch(
            'Auto-refresh',
            True,
            "Automatically refresh the graph when the code changes.\nYou can manually refresh with the refresh button in the top-left corner of the graph."
        )

        self.auto_refresh_timeout = self._number(
            'Auto-refresh timeout',
            5.0,
            min_value=0,
            step=0.1,
            tooltip="How many seconds before an auto-refresh gives up?\nIf it gives up, the refresh button will show that it timed out."
        )

        self.require_manual_refresh = self._switch(
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

        self.percentage = self._switch(
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
            tooltip="2 decimals means 33.33%. -1 decimals means 30%.\nLeaving it blank will round based on python's automatic number display rules."
        )

        self.decimal = self._switch(
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

        self.fraction = self._switch(
            'Fraction',
            False,
            tooltip="Show the odds of a 'pass' in fraction form\nEx: 1/4"
        )

        (
            self.fraction_max_denominator,
            self.fraction_max_denominator_row,
        ) = self._integer(
            'Max denominator size to round to',
            None,
            tooltip="How big should the denominator of the fraction be allowed to be?\nIf you set it to '10', then it will properly show fractions like 1/5 or 1/7,\nbut numbers like 2/11 will be rounded to 1/6 instead."
        )

        self.no_warnings = self._switch(
            'No warnings',
            False,
            tooltip="Don't show messages like:\n- no result\nor\n- converted 'done' cases to 'pass'.\nIf the output box is completely empty, it will automatically hide."
        )

        # ------------------------------------------------------------
        # Graph
        # ------------------------------------------------------------

        self._section('Graph')

        self.no_singleton = self._switch(
            'No singleton',
            False,
            tooltip="If a node has one arrow going in and one arrow going out, it will erase the node and join the arrows directly.\nThis also disables edge labels."
        )

        self.weighted_bubbles = self._switch(
            'Weighted bubbles',
            False,
            tooltip="Show the nodes as circles, where the size of the circle is approximately based on the odds of it occuring."
        )

        self.borders = self._switch(
            'Borders',
            True,
            tooltip="Should nodes have borders?\nIf disabled, this speeds up graph generation."
        )

        self.node_labels = self._switch(
            'Node labels',
            True,
            tooltip="disable text labels on nodes (the ovals on the graph).\nThis speeds up graph generation."
        )

        self.edge_labels = self._switch(
            'Edge labels',
            True,
            tooltip="disable text labels on edges (the arrows on the graph).\nThis speeds up graph generation.\nThis option is disabled if you use the 'no singleton' option."
        )

        self.red = self._choice(
            'Red',
            ['bright', 'faded'],
            'faded',
            tooltip="Which shade of red should it use for the nodes where they are guaranteed to eventually 'fail'?"
        )

        self.green = self._choice(
            'Green',
            ['bright', 'faded'],
            'faded',
            tooltip="Which shade of green should it use for the nodes where they are guaranteed to eventually 'pass'?"
        )

        self.blue = self._choice(
            'Blue',
            ['bright', 'faded'],
            'faded',
            tooltip="Which shade of blue should it use for nodes which don't have a guaranteed outcome?"
        )

        self.grey = self._choice(
            'Grey',
            ['dark', 'light'],
            'light',
            tooltip="Which shade of grey should it use for nodes which were omitted from the odds calculation because they failed a 'bychance' check?"
        )

        self.color_edges = self._choice(
            'Color edges',
            ['same as child', 'darker than child', 'leave black'],
            'leave black',
            tooltip="either:\n1. A red arrow points to a red node,\n2. A dark red arrow points to a red node,\n3. All arrows are black\nThis setting is good for giant graphs, since it turns zoomed-out sections into textureless colored blobs."
        )

        self.automark = self._choice(
            'Auto-marking',
            ['full', 'simple'],
            'full',
            tooltip="Using commands like:\n! ""hello""\nyou can manually configure the node labels.\nIf you have no '!' commands, it adds in nodes after each line of code containing a 'select' statement.\nIn 'full' mode, it adds the name of the variable and the value.\nIn 'simple' mode, it only adds the value."
        )

        self._update_dependencies()

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
            ui.label(label).classes('flex-grow')
            self._help_button(tooltip)

        switch.on_value_change(self._changed)

        return switch

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
            auto_refresh_timeout=self.auto_refresh_timeout.value,
            require_manual_refresh=self.require_manual_refresh.value,
            manual_refresh_timeout=self.manual_refresh_timeout.value,

            percentage=self.percentage.value,
            percentage_decimals=self.percentage_decimals.value,
            decimal=self.decimal.value,
            decimal_decimals=self.decimal_decimals.value,
            fraction=self.fraction.value,
            fraction_max_denominator=self.fraction_max_denominator.value,
            no_warnings=self.no_warnings.value,

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

            self._update_dependencies()

        finally:
            self._updating = False

    # ----------------------------------------------------------------
    # Dependencies
    # ----------------------------------------------------------------

    def _update_dependencies(self):
        # "No singleton" disables edge labels.
        self.edge_labels.enabled = not self.no_singleton.value

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
            self._on_change(self.get_state())