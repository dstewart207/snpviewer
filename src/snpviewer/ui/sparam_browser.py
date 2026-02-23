"""UI integration widget for browsing S-parameter traces."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QFormLayout, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from snpviewer.plotting.sparam_plot import DisplayMode, SParameterPlotWidget


class SParameterBrowserWidget(QWidget):
    """Composite widget exposing trace and display controls with a plot canvas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.trace_list = QListWidget(self)
        self.trace_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.display_combo = QComboBox(self)
        for mode in DisplayMode:
            self.display_combo.addItem(mode.value, mode)

        self.plot_widget = SParameterPlotWidget(self)

        controls = QFormLayout()
        controls.addRow("Display mode:", self.display_combo)
        controls.addRow("Traces:", self.trace_list)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.plot_widget)

        self.display_combo.currentIndexChanged.connect(self._on_display_mode_changed)
        self.trace_list.itemSelectionChanged.connect(self._on_trace_selection_changed)

    def set_network(self, network: object) -> None:
        """Set network and auto-populate available Sij traces from its shape."""

        self.plot_widget.set_network(network)
        self.trace_list.clear()

        for label in self.plot_widget.available_trace_labels():
            self.trace_list.addItem(QListWidgetItem(label))

        if self.trace_list.count() > 0:
            self.trace_list.item(0).setSelected(True)
        self._sync_plot_selection()

    def _on_display_mode_changed(self, _index: int) -> None:
        mode = self.display_combo.currentData(Qt.ItemDataRole.UserRole)
        if isinstance(mode, DisplayMode):
            self.plot_widget.set_display_mode(mode)

    def _on_trace_selection_changed(self) -> None:
        self._sync_plot_selection()

    def _sync_plot_selection(self) -> None:
        labels = [item.text() for item in self.trace_list.selectedItems()]
        self.plot_widget.set_selected_trace_labels(labels)
