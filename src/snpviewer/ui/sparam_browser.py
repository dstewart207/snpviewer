"""UI integration for interactive S-parameter browsing."""

from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QFormLayout, QVBoxLayout, QWidget

from snpviewer.plotting.sparam_plot import DisplayMode, SParameterPlotWidget


class SParameterBrowserWidget(QWidget):
    """High-level UI wrapper that exposes parameter/mode controls + plot."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.plot_widget = SParameterPlotWidget(self)

        self.parameter_combo = QComboBox(self)
        self.display_combo = QComboBox(self)

        self.display_combo.addItem(DisplayMode.MAG_DB.value, DisplayMode.MAG_DB)
        self.display_combo.addItem(DisplayMode.PHASE_DEG.value, DisplayMode.PHASE_DEG)
        self.display_combo.addItem(DisplayMode.REAL.value, DisplayMode.REAL)
        self.display_combo.addItem(DisplayMode.IMAG.value, DisplayMode.IMAG)

        form = QFormLayout()
        form.addRow("Parameter:", self.parameter_combo)
        form.addRow("Mode:", self.display_combo)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.plot_widget)

        self.parameter_combo.currentTextChanged.connect(self._on_parameter_change)
        self.display_combo.currentIndexChanged.connect(self._on_mode_change)

    def set_network(self, network: object) -> None:
        """Set a network and auto-populate all available Sij traces."""

        self.plot_widget.set_network(network)
        self.parameter_combo.clear()
        for trace in self.plot_widget._trace_map:
            self.parameter_combo.addItem(trace.label)

        if self.parameter_combo.count() > 0:
            self.parameter_combo.setCurrentIndex(0)

    def _on_parameter_change(self, label: str) -> None:
        if label:
            self.plot_widget.set_selected_trace_labels([label])
            self.plot_widget.refresh_plot()

    def _on_mode_change(self, _index: int) -> None:
        mode = self.display_combo.currentData()
        if mode is None:
            return
        idx = self.plot_widget.display_mode_combo.findData(mode)
        if idx >= 0:
            self.plot_widget.display_mode_combo.setCurrentIndex(idx)
        else:
            self.plot_widget.refresh_plot()
