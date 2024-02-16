from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pybehave.Workstation.WorkstationGUI import WorkstationGUI


from PyQt5.QtWidgets import QMessageBox, QCheckBox
from PyQt5.QtCore import Qt


class ErrorMessageBox(QMessageBox):
    def __init__(self, wsg: WorkstationGUI, message: str):
        super().__init__()
        self.wsg = wsg

        self.setIcon(QMessageBox.Critical)
        self.setText(message)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.setWindowTitle("Error")
        self.ignore_cb = QCheckBox("Ignore future errors")
        self.ignore_cb.stateChanged.connect(self.on_ignore_errors_changed)
        self.finished.connect(self.on_error_close)
        self.setCheckBox(self.ignore_cb)

    def on_error_close(self):
        self.wsg.emsg = None

    def on_ignore_errors_changed(self, state):
        self.wsg.ignore_errors = (state == Qt.Checked)
