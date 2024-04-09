from __future__ import annotations

import bisect
import copy
import importlib
import os
import pkgutil
from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QTableWidget, QPushButton, QHBoxLayout, \
    QTableWidgetItem, QMessageBox, QFileDialog

from pybehave.Workstation.ComboBox import ComboBox
from pybehave.Workstation.FileCreationTable import FileCreationTable

if TYPE_CHECKING:
    from pybehave.Workstation.WorkstationGUI import WorkstationGUI

import pybehave.Components


class NoBlankSpaceAtBottomEvenlySplitTableView(QTableWidget):
    def sizeHint(self):
        w = self.verticalHeader().width() + 4  # +4 seems to be needed
        for i in range(self.columnCount()):
            w += self.columnWidth(i)
        height = 0
        if self.horizontalHeader().isVisible():
            height += self.horizontalHeader().height()
        height += self.verticalHeader().length() + self.frameWidth() * 2
        return QSize(w, height)


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


class AddressFileCreationDialog(QDialog):
    def __init__(self, wsg: WorkstationGUI, task: str, file_path: str = None):
        super().__init__()

        self.wsg = wsg

        task_module = importlib.import_module("Local.Tasks." + task)
        self.task = getattr(task_module, task)

        self.components = self.task.get_components()
        self.available_components = {}
        for key in self.components:
            if len(self.components[key]) > 1:
                self.available_components[key] = [str(i) for i in range(len(self.components[key]))]
            else:
                self.available_components[key] = None

        for f in pkgutil.iter_modules(pybehave.Components.__path__):
            if f.name[0].isupper():
                importlib.import_module("pybehave.Components." + f.name, f.name)

        if file_path is None:
            self.setWindowTitle("New " + task + " AddressFile")
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

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Component", "Type", "Source", "Address", "Index", "Metadata"])
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

        self.addresses = []

        self.error = None
        self.save_dialog = None

    def save(self):
        if any(len(a[3].text()) == 0 for a in self.addresses):
            self.error = QMessageBox()
            self.error.setIcon(QMessageBox.Critical)
            self.error.setText("Addresses cannot be blank.")
            self.error.setWindowTitle("Error")
            self.error.show()
            return
        address_file = "addresses = AddressFile()\n"
        for address in self.addresses:
            address_file += "addresses.add_component("
            address_file += "\"" + address[0].currentText() + "\", "
            address_file += "\"" + address[1].currentText() + "\", "
            address_file += "\"" + address[2].currentText() + "\", "
            address_file += address[3].text() + ", "
            if address[4] is None:
                address_file += "None, "
            else:
                address_file += address[4].currentText() + ", "
            if address[5] is None:
                address_file += "{}"
            else:
                metadata = {}
                for c in range(address[5].columnCount()):
                    metadata[address[5].horizontalHeaderItem(c).text()] = address[5].item(0, c).text()
                address_file += "{" + ", ".join([f"\'{k}\': {v}" for k, v in metadata.items()]) + "}"
            address_file += ")\n"

        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        # Create the AddressFile folder if it does not already exist
        if not os.path.exists("{}/py-behav/{}/AddressFiles".format(desktop, self.task.__name__)):
            os.makedirs("{}/py-behav/Configurations/".format(desktop))
        self.save_dialog = QFileDialog(self)
        self.save_dialog.setFileMode(QFileDialog.AnyFile)
        self.save_dialog.setViewMode(QFileDialog.List)
        self.save_dialog.setAcceptMode(QFileDialog.AcceptSave)
        self.save_dialog.setNameFilter('Python files (*.py)')
        self.save_dialog.setDirectory("{}/py-behav/{}/AddressFiles".format(desktop, self.task.__name__))
        self.save_dialog.selectFile(
            '{}-Addresses.py'.format(self.task.__name__))
        self.save_dialog.setWindowTitle('Save AddressFile')
        self.save_dialog.accept = lambda: self.save_address_file(address_file)
        self.save_dialog.show()

    def save_address_file(self, file_contents):
        if len(self.save_dialog.selectedFiles()[0]) > 0:  # If a file was selected
            with open(self.save_dialog.selectedFiles()[0], "w", newline='') as out:
                out.write(file_contents)
            super().accept()
        super(QFileDialog, self.save_dialog).accept()

    def add_row(self):
        if len(self.available_components) > 0:
            self.addresses.append([])
            self.table.insertRow(self.table.rowCount())
            add_ind = self.table.rowCount() - 1

            component = ComboBox()
            self.addresses[-1].append(component)
            self.table.setCellWidget(add_ind, 0, component)

            comp_type = ComboBox()
            self.addresses[-1].append(comp_type)
            self.table.setCellWidget(add_ind, 1, comp_type)

            source = ComboBox()
            source.currentTextChanged.connect(lambda:  self.update_metadata(add_ind))
            self.addresses[-1].append(source)
            self.table.setCellWidget(add_ind, 2, source)

            address = QTableWidgetItem()
            self.addresses[-1].append(address)
            self.table.setItem(add_ind, 3, address)

            component.new_signal.connect(lambda: self.component_changed(add_ind))
            component.addItems(self.available_components.keys())
            self.component_changed(add_ind)
            component.lastSelected = component.currentText()
            source.addItems(self.wsg.workstation.sources.keys())
            comp_type.currentTextChanged.connect(lambda: self.update_metadata(add_ind))

        if not self.available_components:
            self.add_button.setEnabled(False)

    def remove_row(self):
        component = self.addresses[self.current_row][0]
        if component.currentText() not in self.available_components:
            if self.addresses[self.current_row][4] is None:
                self.available_components[component.currentText()] = None
            else:
                self.available_components[component.currentText()] = [self.addresses[self.current_row][4].currentText()]
        else:
            bisect.insort(self.available_components[component.currentText()], self.addresses[self.current_row][4].currentText())
        for i in range(self.table.rowCount()):
            if i != self.current_row and self.addresses[i][0].currentText() == component.currentText():
                self.replace_indices(i, component.currentText())
        del self.addresses[self.current_row]
        self.table.removeRow(self.current_row)
        self.current_row = -1
        self.remove_button.setDisabled(True)

    def component_changed(self, add_ind):
        # Remove the new value from the other combo boxes
        component = self.addresses[add_ind][0]
        indices = copy.copy(self.available_components[component.currentText()])
        if indices is None:
            del self.available_components[component.currentText()]
            for i in range(self.table.rowCount()):
                if i != add_ind:
                    self.addresses[i][0].removeItem(self.addresses[i][0].findText(component.currentText()))
        else:
            del self.available_components[component.currentText()][0]
            if len(self.available_components[component.currentText()]) == 0:
                del self.available_components[component.currentText()]
                for i in range(self.table.rowCount()):
                    if i != add_ind and self.addresses[i][0].currentText() != component.currentText():
                        self.addresses[i][0].removeItem(self.addresses[i][0].findText(component.currentText()))

        # Add the previous value back into the other combo boxes
        if component.lastSelected is not None:
            for i in range(self.table.rowCount()):
                if i != add_ind and self.addresses[i][0].findText(component.lastSelected) == -1:
                    self.addresses[i][0].addItem(component.lastSelected)
            index = self.addresses[add_ind][4]
            if component.lastSelected not in self.available_components:
                if isinstance(index, ComboBox):
                    self.available_components[component.lastSelected] = [index.currentText()]
                else:
                    self.available_components[component.lastSelected] = None
            else:
                bisect.insort(self.available_components[component.lastSelected], index.currentText())

            # Add new indices back into any corresponding combo boxes
            for i in range(self.table.rowCount()):
                if i != add_ind and self.addresses[i][0].currentText() == component.lastSelected:
                    self.replace_indices(i, component.lastSelected)

        # Update index column
        if indices is not None:
            index = ComboBox()
            index.addItems(indices)
            index.new_signal.connect(lambda: self.update_indices(add_ind))
            if len(self.addresses[add_ind]) < 5:
                self.addresses[add_ind].append(index)
            else:
                self.addresses[add_ind][4] = index
            self.table.setCellWidget(add_ind, 4, index)
            self.update_indices(add_ind)
            index.lastSelected = index.currentText()
            super_type = self.components[component.currentText()][int(index.currentText())]
        else:
            index = QTableWidgetItem()
            index.setFlags(QtCore.Qt.ItemIsEnabled)
            if len(self.addresses[add_ind]) < 5:
                self.addresses[add_ind].append(None)
            else:
                self.addresses[add_ind][4] = None
            self.table.removeCellWidget(add_ind, 4)
            self.table.setItem(add_ind, 4, index)
            super_type = self.components[component.currentText()][0]

        # Update component type column
        subclasses = get_all_subclasses(super_type)
        subclasses.insert(0, super_type)
        subclasses = [s.__name__ for s in subclasses]
        self.addresses[add_ind][1].clear()
        self.addresses[add_ind][1].addItems(subclasses)

    def update_indices(self, add_ind):
        component = self.addresses[add_ind][0]
        # Remove new index from any corresponding combo boxes
        if component.currentText() in self.available_components:
            indices = self.available_components[component.currentText()]
            if self.addresses[add_ind][4].currentText() in indices:
                del indices[indices.index(self.addresses[add_ind][4].currentText())]
        for i in range(self.table.rowCount()):
            if i != add_ind and self.addresses[i][0].currentText() == component.currentText():
                self.addresses[i][4].removeItem(self.addresses[i][4].findText(self.addresses[add_ind][4].currentText()))
        # Add old index back into any corresponding combo boxes
        prev_ind = self.addresses[add_ind][4].lastSelected
        if prev_ind is not None:
            bisect.insort(self.available_components[component.currentText()], prev_ind)
            for i in range(self.table.rowCount()):
                if i != add_ind and self.addresses[i][0].currentText() == component.lastSelected:
                    self.replace_indices(i, component.currentText())

    def replace_indices(self, i, c_name):
        # Replace indices in combo box with the available ones
        cur_ind = self.addresses[i][4].currentText()
        self.addresses[i][4].clear()
        new_indices = copy.copy(self.available_components[c_name])
        bisect.insort(new_indices, cur_ind)
        self.addresses[i][4].addItems(new_indices)
        self.addresses[i][4].setCurrentText(cur_ind)

    def update_metadata(self, add_ind):
        defaults = self.wsg.workstation.sources[self.addresses[add_ind][2].currentText()].metadata_defaults()
        if self.addresses[add_ind][4] is None:
            super_type = self.components[self.addresses[add_ind][0].currentText()][0]
        else:
            super_type = self.components[self.addresses[add_ind][0].currentText()][int(self.addresses[add_ind][4].currentText())]
        subclasses = get_all_subclasses(super_type)
        subclasses.insert(0, super_type)
        defaults.update(subclasses[self.addresses[add_ind][1].currentIndex()].metadata_defaults())
        if defaults:
            metadata = NoBlankSpaceAtBottomEvenlySplitTableView()
            metadata.verticalHeader().setVisible(False)
            metadata.setColumnCount(len(defaults))
            metadata.setHorizontalHeaderLabels(defaults.keys())
            metadata.insertRow(metadata.rowCount())
            for i, val in enumerate(defaults.values()):
                metadata.setItem(0, i, QTableWidgetItem(str(val) if not isinstance(val, str) else f"\"{val}\""))
            metadata.resizeRowsToContents()
            if len(self.addresses[add_ind]) < 6:
                self.addresses[add_ind].append(metadata)
            else:
                self.addresses[add_ind][5] = metadata
            self.table.setCellWidget(add_ind, 5, metadata)
        else:
            metadata = QTableWidgetItem()
            metadata.setFlags(QtCore.Qt.ItemIsEnabled)
            if len(self.addresses[add_ind]) < 6:
                self.addresses[add_ind].append(None)
            else:
                self.addresses[add_ind][5] = None
            self.table.removeCellWidget(add_ind, 5)
            self.table.setItem(add_ind, 5, metadata)
        self.table.resizeRowToContents(add_ind)
        self.table.resizeColumnToContents(5)
