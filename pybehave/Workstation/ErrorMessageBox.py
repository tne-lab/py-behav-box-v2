from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pybehave.Workstation.WorkstationGUI import WorkstationGUI


from PyQt5.QtWidgets import QMessageBox, QCheckBox
from PyQt5.QtCore import Qt


class ErrorMessageBox(QMessageBox):
    def __init__(self, wsg: WorkstationGUI, message: str, error_type: str):
        super().__init__()
        self.wsg = wsg

        self.setInformativeText(message)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        if error_type == "GUI":
            self.setIcon(QMessageBox.Warning)
            self.setWindowTitle("Error in GUI")
            self.setText("The task could still be running but the GUI may no longer update properly.")
        elif error_type == "Stop":
            self.setIcon(QMessageBox.Warning)
            self.setWindowTitle("Error While Stopping Task")
            self.setText("Some components may not have turned off correctly.")
        elif error_type == "Clear":
            self.setIcon(QMessageBox.Warning)
            self.setWindowTitle("Error While Clearing Task")
            self.setText("Some components may not have reset correctly.")
        elif error_type == "Source Non-Fatal":
            self.setIcon(QMessageBox.Warning)
            self.setWindowTitle("Error in Component")
            self.setText("A component has experienced an error and the corresponding task will stop but other tasks and components may still be functional.")
        elif error_type == "Source Fatal":
            self.setIcon(QMessageBox.Critical)
            self.setWindowTitle("Error in Source")
            self.setText("A fatal exception has occurred in a Source. All tasks using the Source will stop and the Source will have to be reset before continuing.")
        else:
            self.setIcon(QMessageBox.Critical)
            self.setWindowTitle("Error in Task")
            self.setText("A fatal exception has occurred while running the task and it has stopped.")
        self.ignore_cb = QCheckBox("Ignore future errors")
        self.ignore_cb.stateChanged.connect(self.on_ignore_errors_changed)
        self.finished.connect(self.on_error_close)
        self.setCheckBox(self.ignore_cb)

    def on_error_close(self):
        self.wsg.emsgs.remove(self)

    def on_ignore_errors_changed(self, state):
        self.wsg.ignore_errors = (state == Qt.Checked)
