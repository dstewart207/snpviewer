"""Qt application bootstrap utilities for snpviewer."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class SnpViewerWindow(QMainWindow):
    """Main application window for snpviewer."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SNP Viewer")
        self.resize(960, 640)
        self.setCentralWidget(QLabel("SNP Viewer is ready."))


def run() -> int:
    """Start the Qt application event loop."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = SnpViewerWindow()
    window.show()
    return app.exec()
