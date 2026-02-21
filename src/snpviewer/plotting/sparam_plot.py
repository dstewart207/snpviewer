"""Qt-embedded matplotlib plotting for S-parameter traces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class DisplayMode(str, Enum):
    """Display modes for complex S-parameter data."""

    MAG_DB = "|S| dB"
    PHASE_DEG = "Phase (deg)"
    REAL = "Real"
    IMAG = "Imag"


@dataclass(frozen=True)
class TraceSelection:
    """Represents an Sij trace selection."""

    i: int
    j: int

    @property
    def label(self) -> str:
        return f"S{self.i + 1}{self.j + 1}"


class SParameterPlotWidget(QWidget):
    """Combined controls + matplotlib canvas for browsing S-parameters."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._network = None
        self._trace_map: list[TraceSelection] = []

        self.trace_list = QListWidget(self)
        self.trace_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        self.display_mode_combo = QComboBox(self)
        for mode in DisplayMode:
            self.display_mode_combo.addItem(mode.value, mode)

        self.figure = Figure(constrained_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(1, 1, 1)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Display:"))
        controls_layout.addWidget(self.display_mode_combo)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Trace (Sij):"))
        layout.addWidget(self.trace_list)
        layout.addLayout(controls_layout)
        layout.addWidget(self.canvas, 1)

        self.trace_list.currentRowChanged.connect(lambda _idx: self.refresh_plot())
        self.display_mode_combo.currentIndexChanged.connect(lambda _idx: self.refresh_plot())

    def set_network(self, network: object) -> None:
        """Set a scikit-rf-like network object and populate available traces.

        Expected attributes:
        - ``network.s`` complex ndarray with shape ``(n_freq, n_port, n_port)``
        - ``network.f`` frequency ndarray in Hz
        """

        self._network = network
        self._populate_traces_from_network()
        self.refresh_plot()

    def _populate_traces_from_network(self) -> None:
        self.trace_list.clear()
        self._trace_map.clear()

        if self._network is None:
            return

        n_ports = int(self._network.s.shape[1])
        for i in range(n_ports):
            for j in range(n_ports):
                selection = TraceSelection(i=i, j=j)
                self._trace_map.append(selection)
                self.trace_list.addItem(QListWidgetItem(selection.label))

        if self._trace_map:
            self.trace_list.setCurrentRow(0)

    def current_display_mode(self) -> DisplayMode:
        mode = self.display_mode_combo.currentData(Qt.ItemDataRole.UserRole)
        return mode if isinstance(mode, DisplayMode) else DisplayMode.MAG_DB

    def selected_traces(self) -> Sequence[TraceSelection]:
        row = self.trace_list.currentRow()
        if row < 0 or row >= len(self._trace_map):
            return []
        return [self._trace_map[row]]

    def refresh_plot(self) -> None:
        self.axes.clear()

        if self._network is None:
            self.axes.set_title("No network loaded")
            self.canvas.draw_idle()
            return

        freq_hz = np.asarray(self._network.f)
        freq_ghz = freq_hz / 1e9
        display_mode = self.current_display_mode()

        for trace in self.selected_traces():
            complex_values = np.asarray(self._network.s[:, trace.i, trace.j])
            y_data, y_label = self._format_trace(complex_values, display_mode)
            self.axes.plot(freq_ghz, y_data, label=trace.label)

        self.axes.set_xlabel("Frequency (GHz)")
        self.axes.set_ylabel(y_label if self.selected_traces() else "Value")
        self.axes.legend()
        self.axes.grid(True, alpha=0.3)
        self.canvas.draw_idle()

    @staticmethod
    def _format_trace(values: np.ndarray, mode: DisplayMode) -> tuple[np.ndarray, str]:
        if mode == DisplayMode.MAG_DB:
            magnitude = np.maximum(np.abs(values), 1e-16)
            return 20 * np.log10(magnitude), "Magnitude (dB)"
        if mode == DisplayMode.PHASE_DEG:
            return np.angle(values, deg=True), "Phase (deg)"
        if mode == DisplayMode.REAL:
            return np.real(values), "Real"
        if mode == DisplayMode.IMAG:
            return np.imag(values), "Imag"
        raise ValueError(f"Unsupported display mode: {mode}")

    def set_selected_trace_labels(self, labels: Iterable[str]) -> None:
        """Select a trace by label (e.g., ``S21``) for external UI integration."""

        label_set = set(labels)
        for idx, trace in enumerate(self._trace_map):
            if trace.label in label_set:
                self.trace_list.setCurrentRow(idx)
                break
