from __future__ import annotations

from sortedcontainers import SortedList
import importlib
import os
import runpy
from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QPushButton, QHBoxLayout, \
    QTableWidgetItem, QFileDialog

from pybehave.Workstation.ComboBox import ComboBox
from pybehave.Workstation.FileCreationTable import FileCreationTable
import pybehave.Utilities.Exceptions as pyberror

if TYPE_CHECKING:
    from pybehave.Workstation.WorkstationGUI import WorkstationGUI


class ProtocolCreationDialog(QDialog):
    def __init__(self, wsg: WorkstationGUI, task: str, file_path: str = None):
        super().__init__()

        self.wsg = wsg
        self.file_path = file_path

        task_module = importlib.import_module("Local.Tasks." + task)
        self.task = getattr(task_module, task)

        self.constant_dict = self.task.get_constants()
        keys = list(self.constant_dict.keys())
        self.available_constants = SortedList(self.constant_dict.keys(), key=lambda x: keys.index(x))

        if file_path is None:
            self.setWindowTitle("New " + task + " Protocol")
        else:
            self.setWindowTitle("Edit " + task + " Protocol")
        self.setMinimumSize(500, 700)
        control = QDialogButtonBox.Save | QDialogButtonBox.Cancel

        button_layout = QHBoxLayout()
        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.save)
        self.control_buttons.rejected.connect(self.reject)
        self.row_buttons = QDialogButtonBox()
        self.add_button = QPushButton("+")
        self.add_button.clicked.connect(self.add_row)
        self.remove_button = QPushButton("−")
        self.remove_button.clicked.connect(self.remove_row)
        self.remove_button.setEnabled(False)
        self.row_buttons.addButton(self.add_button, QDialogButtonBox.ActionRole)
        self.row_buttons.addButton(self.remove_button, QDialogButtonBox.ActionRole)
        button_layout.addWidget(self.row_buttons, alignment=QtCore.Qt.AlignLeft)
        button_layout.addWidget(self.control_buttons, alignment=QtCore.Qt.AlignRight)

        self.layout = QVBoxLayout()
        self.table = FileCreationTable()

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Constant", "Value"])
        self.table.verticalHeader().setVisible(False)
        self.table.deselected_signal.connect(lambda: self.remove_button.setDisabled(True))
        self.current_row = None

        def update_row():
            self.remove_button.setDisabled(False)
            self.current_row = self.table.currentRow()

        self.table.clicked.connect(update_row)

        self.layout.addWidget(self.table)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.constants = []

        self.save_dialog = None
        QTimer.singleShot(1, self.load_protocol_file)

    def load_protocol_file(self):
        if self.file_path is not None:
            try:
                file_globals = runpy.run_path(self.file_path)
            except:
                raise pyberror.MalformedProtocolError
            for cons in file_globals['protocol']:
                if cons in self.constant_dict:
                    self.add_row()
                    self.constants[-1][0].setCurrentText(cons)
                    val = file_globals['protocol'][cons]
                    self.constants[-1][1].setText(f'\"{val}\"' if isinstance(val, str) else str(val))

    def save(self):
        protocol = "protocol = {"
        for constant in self.constants:
            protocol += f"\'{constant[0].currentText()}\': {str(constant[1].text())},\n"
        protocol += '}'

        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        # Create the Protocol folder if it does not already exist
        if not os.path.exists("{}/py-behav/{}/Protocols".format(desktop, self.task.__name__)):
            os.makedirs("{}/py-behav/{}/Protocols".format(desktop, self.task.__name__))
        self.save_dialog = QFileDialog(self)
        self.save_dialog.setFileMode(QFileDialog.AnyFile)
        self.save_dialog.setViewMode(QFileDialog.List)
        self.save_dialog.setAcceptMode(QFileDialog.AcceptSave)
        self.save_dialog.setNameFilter('Python files (*.py)')
        self.save_dialog.setDirectory("{}/py-behav/{}/Protocols".format(desktop, self.task.__name__))
        self.save_dialog.selectFile(
            '{}-Protocol.py'.format(self.task.__name__))
        self.save_dialog.setWindowTitle('Save AddressFile')
        self.save_dialog.accept = lambda: self.save_protocol(protocol)
        self.save_dialog.show()

    def save_protocol(self, file_contents):
        if len(self.save_dialog.selectedFiles()[0]) > 0:  # If a file was selected
            filename = self.save_dialog.selectedFiles()[0]
            filename = filename if filename.endswith('.py') else filename + '.py'
            with open(filename, "w", newline='') as out:
                out.write(file_contents)
            super().accept()
        super(QFileDialog, self.save_dialog).accept()

    def add_row(self):
        if len(self.available_constants) > 0:
            self.constants.append([])
            self.table.insertRow(self.table.rowCount())
            add_ind = self.table.rowCount() - 1

            constant = ComboBox()
            self.constants[-1].append(constant)
            self.table.setCellWidget(add_ind, 0, constant)

            value = QTableWidgetItem()
            self.constants[-1].append(value)
            self.table.setItem(add_ind, 1, value)

            constant.new_signal.connect(lambda: self.constant_changed(add_ind))
            constant.addItems(self.available_constants)
            self.constant_changed(add_ind)
            constant.lastSelected = constant.currentText()

        if not self.available_constants:
            self.add_button.setEnabled(False)

    def remove_row(self):
        constant = self.constants[self.current_row][0]
        self.available_constants.add(constant.currentText())
        for i in range(self.table.rowCount()):  # Should ideally be insorted
            if i != self.current_row:
                self.constants[i][0].addItem(constant.currentText())
        del self.constants[self.current_row]
        self.table.removeRow(self.current_row)
        self.current_row = -1
        self.remove_button.setDisabled(True)

    def constant_changed(self, add_ind):
        # Remove the new value from the other combo boxes
        constant = self.constants[add_ind][0]
        del self.available_constants[self.available_constants.index(constant.currentText())]
        for i in range(self.table.rowCount()):
            if i != add_ind:
                self.constants[i][0].removeItem(self.constants[i][0].findText(constant.currentText()))

        # Add the previous value back into the other combo boxes
        if constant.lastSelected is not None:
            self.available_constants.add(constant.lastSelected)
            for i in range(self.table.rowCount()):  # Should ideally be insorted
                if i != add_ind:
                    self.constants[i][0].addItem(constant.lastSelected)

        # Update the constant value column
        default_value = self.constant_dict[constant.currentText()]
        self.constants[add_ind][1].setText(f'\"{default_value}\"' if isinstance(default_value, str) else str(default_value))
