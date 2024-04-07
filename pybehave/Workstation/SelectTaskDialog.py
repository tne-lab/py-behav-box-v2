from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pybehave.Workstation.WorkstationGUI import WorkstationGUI

from PyQt5.QtWidgets import *
import pkgutil
import os


class SelectTaskDialog(QDialog):
    def __init__(self, wsg: WorkstationGUI, is_addressfile: bool):
        super().__init__()

        self.is_addressfile = is_addressfile
        self.wsg = wsg
        self.setWindowTitle("Select Task")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        task_box = QGroupBox('Task')
        task_box_layout = QHBoxLayout(self)
        task_box.setLayout(task_box_layout)
        self.task = QComboBox()
        self.tasks = []
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        for f in pkgutil.iter_modules([f'{desktop}/py-behav/Local/Tasks']):
            self.tasks.append(f.name)
        self.task.addItems(self.tasks)
        task_box_layout.addWidget(self.task)
        self.layout.addWidget(task_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def accept(self) -> None:
        super().accept()
        if self.is_addressfile:
            self.wsg.address_file_dialog(self.task.currentText())
        else:
            self.wsg.protocol_dialog(self.task.currentText())
