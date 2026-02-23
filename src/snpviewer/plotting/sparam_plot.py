"""Qt-embedded matplotlib plot widget for S-parameter traces."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class DisplayMode(str, Enum):
    """Supported display modes for complex S-parameter data."""

    MAG_DB = "|S| dB"
    PHASE_DEG = "Phase (deg)"
    REAL = "Real"
    IMAG = "Imag"


class SParameterPlotWidget(QWidget):
    """Matplotlib canvas embedded in Qt for plotting selected S-parameter traces."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._network: object | None = None
        self._display_mode: DisplayMode = DisplayMode.MAG_DB
        self._selected_trace_labels: list[str] = []

        self.figure = Figure(constrained_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(1, 1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def set_network(self, network: object | None) -> None:
        """Set a scikit-rf-like network object.

        Network shape is expected to be ``network.s.shape == (n_freq, n_port, n_port)``
        and frequencies are expected in ``network.f`` as Hz.
        """

        self._network = network
        if network is None:
            self._selected_trace_labels = []
        elif not self._selected_trace_labels:
            labels = self.available_trace_labels()
            if labels:
                self._selected_trace_labels = [labels[0]]
        self.refresh_plot()

    def set_display_mode(self, mode: DisplayMode) -> None:
        self._display_mode = mode
        self.refresh_plot()

    def set_selected_trace_labels(self, labels: Iterable[str]) -> None:
        self._selected_trace_labels = list(labels)
        self.refresh_plot()

    def available_trace_labels(self) -> list[str]:
        """Return Sij labels generated from ``network.s.shape`` for n-port data."""

        if self._network is None:
            return []

        s_matrix = np.asarray(self._network.s)
        if s_matrix.ndim != 3:
            return []

        n_ports = int(s_matrix.shape[1])
        return [f"S{i + 1}{j + 1}" for i in range(n_ports) for j in range(n_ports)]

    def refresh_plot(self) -> None:
        self.axes.clear()

        if self._network is None:
            self.axes.set_title("No network loaded")
            self.canvas.draw_idle()
            return

        freq_ghz = np.asarray(self._network.f, dtype=float) / 1e9
        ylabel = "Value"

        for trace_label in self._selected_trace_labels:
            parsed = self._parse_trace_label(trace_label)
            if parsed is None:
                continue

            i_idx, j_idx = parsed
            complex_values = np.asarray(self._network.s[:, i_idx, j_idx])
            y_data, ylabel = self._format_trace(complex_values, self._display_mode)
            self.axes.plot(freq_ghz, y_data, label=trace_label)

        self.axes.set_xlabel("Frequency (GHz)")
        self.axes.set_ylabel(ylabel)
        if self.axes.lines:
            self.axes.legend()
        self.axes.grid(True, alpha=0.3)
        self.canvas.draw_idle()

    @staticmethod
    def _parse_trace_label(label: str) -> tuple[int, int] | None:
        if len(label) != 3 or not label.startswith("S"):
            return None
        if not (label[1].isdigit() and label[2].isdigit()):
            return None
        return int(label[1]) - 1, int(label[2]) - 1

    @staticmethod
    def _format_trace(values: np.ndarray, mode: DisplayMode) -> tuple[np.ndarray, str]:
        if mode is DisplayMode.MAG_DB:
            magnitude = np.maximum(np.abs(values), 1e-16)
            return 20.0 * np.log10(magnitude), "Magnitude (dB)"
        if mode is DisplayMode.PHASE_DEG:
            return np.angle(values, deg=True), "Phase (deg)"
        if mode is DisplayMode.REAL:
            return np.real(values), "Real"
        if mode is DisplayMode.IMAG:
            return np.imag(values), "Imag"
        raise ValueError(f"Unsupported display mode: {mode}")
