"""Qt main window for loading and summarizing Touchstone files."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QWidget,
)

from snpviewer.services.network_service import NetworkService, NetworkSummary


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self, network_service: NetworkService | None = None) -> None:
        super().__init__()
        self._network_service = network_service or NetworkService()

        self.setWindowTitle("SNP Viewer")
        self.resize(760, 380)

        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self._build_status_bar()
        self._build_summary_panel()

    def _build_actions(self) -> None:
        self.open_touchstone_action = QAction("Open Touchstone…", self)
        self.open_touchstone_action.setStatusTip("Open a Touchstone network file")
        self.open_touchstone_action.triggered.connect(self._on_open_touchstone)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_touchstone_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("File", self)
        toolbar.setMovable(False)
        toolbar.addAction(self.open_touchstone_action)
        self.addToolBar(toolbar)

    def _build_status_bar(self) -> None:
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

    def _build_summary_panel(self) -> None:
        container = QWidget(self)
        layout = QFormLayout(container)

        self.file_name_value = QLabel("—")
        self.file_path_value = QLabel("—")
        self.port_count_value = QLabel("—")
        self.freq_range_value = QLabel("—")
        self.point_count_value = QLabel("—")

        layout.addRow("File name", self.file_name_value)
        layout.addRow("Path", self.file_path_value)
        layout.addRow("Ports", self.port_count_value)
        layout.addRow("Frequency range", self.freq_range_value)
        layout.addRow("Points", self.point_count_value)

        self.setCentralWidget(container)

    def _on_open_touchstone(self) -> None:
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Touchstone File",
            "",
            "Touchstone Files (*.s*p);;All Files (*)",
        )
        if not selected_path:
            return

        try:
            summary = self._network_service.load_touchstone(selected_path)
        except (ValueError, OSError) as exc:
            self._show_load_error(selected_path, str(exc))
            self.statusBar().showMessage("Failed to load Touchstone file", 5000)
            return

        self._update_summary(summary)
        self.statusBar().showMessage(f"Loaded {summary.path.name}", 5000)

    def _update_summary(self, summary: NetworkSummary) -> None:
        self.file_name_value.setText(summary.path.name)
        self.file_path_value.setText(str(summary.path))
        self.port_count_value.setText(str(summary.num_ports))
        self.freq_range_value.setText(
            f"{summary.frequency_start_hz:g} Hz → {summary.frequency_stop_hz:g} Hz"
        )
        self.point_count_value.setText(str(summary.point_count))

    def _show_load_error(self, path: str, reason: str) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Unable to load Touchstone file")
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setText("The selected file could not be loaded.")
        dialog.setInformativeText(
            "Try validating that the file exists, has a Touchstone extension "
            "(.s1p/.s2p/etc.), and is readable. Then retry loading the file."
        )
        dialog.setDetailedText(f"Path: {Path(path)}\n\nDetails: {reason}")
        dialog.exec()
