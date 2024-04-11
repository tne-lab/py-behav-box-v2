from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pybehave.Workstation.WorkstationGUI import WorkstationGUI

from PyQt5.QtWidgets import *
import pkgutil
import os


class SelectTaskDialog(QDialog):
    def __init__(self, wsg: WorkstationGUI, is_addressfile: bool, edit: bool = False):
        super().__init__()

        self.is_addressfile = is_addressfile
        self.edit = edit
        self.wsg = wsg
        self.setWindowTitle("Select Task")

        if not edit:
            control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

            self.control_buttons = QDialogButtonBox(control)
            self.control_buttons.accepted.connect(self.accept)
            self.control_buttons.rejected.connect(self.reject)
        else:
            control = QDialogButtonBox.Cancel

            self.control_buttons = QDialogButtonBox(control)
            load_configuration = QPushButton("Choose File")
            load_configuration.clicked.connect(self.choose_file)
            self.control_buttons.addButton(load_configuration, QDialogButtonBox.ActionRole)
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

        self.choose_dialog = None

    def accept(self) -> None:
        super().accept()
        if self.choose_dialog is None:
            if self.is_addressfile:
                self.wsg.address_file_dialog(self.task.currentText())
            else:
                self.wsg.protocol_dialog(self.task.currentText())
        else:
            super(QFileDialog, self.choose_dialog).accept()
            if self.is_addressfile:
                self.wsg.address_file_dialog(self.task.currentText(), self.choose_dialog.selectedFiles()[0])
            else:
                self.wsg.protocol_dialog(self.task.currentText(), self.choose_dialog.selectedFiles()[0])

    def choose_file(self):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.choose_dialog = QFileDialog(self)
        if self.is_addressfile:
            # Create the AddressFile folder if it does not already exist
            if not os.path.exists("{}/py-behav/{}/AddressFiles".format(desktop, self.task.currentText())):
                os.makedirs("{}/py-behav/{}/AddressFiles".format(desktop, self.task.currentText()))
            self.choose_dialog.setDirectory("{}/py-behav/{}/AddressFiles".format(desktop, self.task.currentText()))
            self.choose_dialog.setWindowTitle('Choose AddressFile')
        else:
            # Create the Protocol folder if it does not already exist
            if not os.path.exists("{}/py-behav/{}/Protocols".format(desktop, self.task.currentText())):
                os.makedirs("{}/py-behav/{}/Protocols".format(desktop, self.task.currentText()))
            self.choose_dialog.setDirectory("{}/py-behav/{}/Protocols".format(desktop, self.task.currentText()))
            self.choose_dialog.setWindowTitle('Choose Protocol')
        self.choose_dialog.setFileMode(QFileDialog.AnyFile)
        self.choose_dialog.setViewMode(QFileDialog.List)
        self.choose_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        self.choose_dialog.setNameFilter('Python files (*.py)')
        self.choose_dialog.accept = lambda: self.accept()
        self.choose_dialog.show()
