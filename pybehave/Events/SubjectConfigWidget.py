import importlib
import os

from PyQt5 import QtCore
from PyQt5.QtCore import QSettings, QTimer, pyqtSlot
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QCheckBox, \
    QListWidget, QListWidgetItem, QComboBox

from pybehave.Events import PybEvents

from pybehave.Events.EventWidget import EventWidget
from pybehave.Workstation.ChamberWidget import ChamberWidget


class SubjectConfigWidget(EventWidget):

    def __init__(self):
        super(SubjectConfigWidget, self).__init__("subject_config")
        self.constant_names = []
        self.combos = []

        self.layout = QVBoxLayout(self)
        self.widget = QGroupBox('Subject Configuration')
        self.layout.addWidget(self.widget)
        self.setLayout(self.layout)
        self.config_layout = QVBoxLayout(self.widget)
        self.controls_layout = QHBoxLayout(self.widget)
        self.specific_layout = QVBoxLayout(self.widget)
        self.protocol_specific = QCheckBox("Protocol Specific")
        self.protocol_specific.stateChanged.connect(lambda _: self.load_keys())
        self.address_specific = QCheckBox("Address File Specific")
        self.address_specific.stateChanged.connect(lambda _: self.load_keys())
        self.specific_layout.addWidget(self.protocol_specific)
        self.specific_layout.addWidget(self.address_specific)
        self.remove_button = QPushButton()
        self.remove_button.setText("−")
        self.remove_button.setFixedWidth(30)
        self.remove_button.setDisabled(True)
        self.remove_button.clicked.connect(self.remove_constant)
        self.add_button = QPushButton()
        self.add_button.setText("+")
        self.add_button.setFixedWidth(30)
        self.add_button.clicked.connect(self.add_constant)
        self.controls_layout.addLayout(self.specific_layout)
        self.controls_layout.addWidget(self.remove_button)
        self.controls_layout.addWidget(self.add_button)
        self.config_layout.addLayout(self.controls_layout)
        constants_name_box = QGroupBox('Name')
        constants_name_layout = QVBoxLayout(self.widget)
        self.constants_name_list = QListWidget()
        # self.constants_name_list.itemClicked.connect(self.on_name_clicked)
        # self.constants_name_list.itemDelegate().commitData.connect(self.on_commit_name)
        constants_name_layout.addWidget(self.constants_name_list)
        constants_name_box.setLayout(constants_name_layout)
        constants_value_box = QGroupBox('Value')
        constants_value_layout = QVBoxLayout(self.widget)
        self.constants_value_list = QListWidget()
        self.constants_value_list.itemClicked.connect(self.on_value_clicked)
        self.constants_value_list.itemDelegate().commitData.connect(self.on_commit_value)
        constants_value_layout.addWidget(self.constants_value_list)
        constants_value_box.setLayout(constants_value_layout)
        lists_layout = QHBoxLayout(self.widget)
        lists_layout.addWidget(constants_name_box)
        lists_layout.addWidget(constants_value_box)
        self.config_layout.addLayout(lists_layout)
        self.widget.setLayout(self.config_layout)

        self.settings = None
        self.names = []

    @pyqtSlot()
    def handle_event(self, event: PybEvents.PybEvent):
        super(SubjectConfigWidget, self).handle_event(event)
        if isinstance(event, PybEvents.OutputFileChangedEvent):
            self.load_keys()

    def load_keys(self):
        self.constants_value_list.clear()
        self.constants_name_list.clear()
        self.combos = []
        self.names = []
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        settings_path = "subjectConfig/" + self.cw.task_name.currentText() + "/"
        if self.protocol_specific.isChecked() and len(self.cw.protocol_path.text()) > 0:
            settings_path += "protocol_" + self.cw.protocol_path.text() + "/"
        if self.address_specific.isChecked() and len(self.cw.address_file_path.text()) > 0:
            settings_path += "address_" + self.cw.address_file_path.text() + "/"
        settings_path += self.cw.subject.text()
        self.settings.beginGroup(settings_path)
        keys = self.settings.childKeys()
        constants = {}
        for key in keys:
            options = list(set(self.constant_names) - set(self.names))
            combo = QComboBox()
            self.combos.append(combo)
            combo.addItems(options)
            combo.setCurrentIndex(options.index(key))
            index = len(self.combos) - 1
            combo.activated.connect(lambda _: self.on_commit_name(index))
            self.names.append(key)
            ql = QListWidgetItem(key, self.constants_name_list)
            self.constants_name_list.setItemWidget(ql, combo)
            # ql.setFlags(ql.flags() | QtCore.Qt.ItemIsEditable)
            ql = QListWidgetItem(self.settings.value(key, ""), self.constants_value_list)
            ql.setFlags(ql.flags() | QtCore.Qt.ItemIsEditable)
            if len(self.settings.value(key, "")) > 0:
                constants[key] = self.settings.value(key, "")
        if len(constants) > 0:
            self.cw.workstation.mainq.send_bytes(
                self.cw.workstation.encoder.encode(PybEvents.ConstantsUpdateEvent(int(self.cw.chamber_id.text()) - 1, constants)))

    def set_chamber(self, cw: ChamberWidget):
        super(SubjectConfigWidget, self).set_chamber(cw)
        task_module = importlib.import_module("Local.Tasks." + self.cw.task_name.currentText())
        task = getattr(task_module, self.cw.task_name.currentText())
        # Get all default values for task constants
        for key in task.get_constants():
            self.constant_names.append(key)
        QTimer.singleShot(0, self.load_keys)

    def remove_constant(self):
        index = self.constants_value_list.currentRow()
        self.settings.remove(self.combos[index].currentText())
        self.cw.workstation.mainq.send_bytes(
            self.cw.workstation.encoder.encode(PybEvents.ConstantRemoveEvent(int(self.cw.chamber_id.text()) - 1,
                                                                             self.combos[index].currentText())))
        option = self.names.pop(index)
        self.add_option(option, index)
        self.combos.pop(index)
        self.constants_value_list.takeItem(index)
        self.constants_name_list.takeItem(index)
        self.remove_button.setDisabled(True)

    def add_constant(self):
        options = list(set(self.constant_names) - set(self.names))
        combo = QComboBox()
        self.combos.append(combo)
        combo.addItems(options)
        index = len(self.combos) - 1
        combo.activated.connect(lambda _: self.on_commit_name(index))
        self.names.append(combo.currentText())
        ql = QListWidgetItem("", self.constants_name_list)
        self.constants_name_list.setItemWidget(ql, combo)
        ql = QListWidgetItem("", self.constants_value_list)
        ql.setFlags(ql.flags() | QtCore.Qt.ItemIsEditable)
        self.constants_name_list.setCurrentRow(len(self.combos)-1)
        self.constants_value_list.setCurrentRow(len(self.combos)-1)
        self.remove_option(combo.currentText(), index)
        self.remove_button.setDisabled(True)

    def on_value_clicked(self, _):
        self.constants_name_list.setCurrentRow(self.constants_value_list.currentRow())
        self.remove_button.setDisabled(False)

    def on_name_clicked(self, _):
        self.constants_value_list.setCurrentRow(self.constants_name_list.currentRow())
        self.remove_button.setDisabled(False)

    def on_commit_name(self, index):
        self.remove_option(self.combos[index].currentText(), index)
        prev = self.names[self.constants_name_list.currentRow()]
        if self.combos[index].currentText() != prev and len(prev) > 0:
            self.add_option(prev, index)
        self.constants_value_list.setCurrentRow(index)
        if len(self.constants_value_list.currentItem().text()) > 0:
            if self.combos[index].currentText() != prev and len(prev) > 0:
                self.settings.remove(prev)
                self.cw.workstation.mainq.send_bytes(
                    self.cw.workstation.encoder.encode(PybEvents.ConstantRemoveEvent(int(self.cw.chamber_id.text()) - 1,
                                                                                     prev)))
            self.settings.setValue(self.combos[index].currentText(), self.constants_value_list.currentItem().text())
            if len(self.constants_value_list.currentItem().text()) > 0:
                self.cw.workstation.mainq.send_bytes(
                    self.cw.workstation.encoder.encode(PybEvents.ConstantsUpdateEvent(int(self.cw.chamber_id.text()) - 1,
                                                       {self.combos[index].currentText(): self.constants_value_list.currentItem().text()})))
        self.names[self.constants_name_list.currentRow()] = self.combos[index].currentText()

    def on_commit_value(self):
        index = self.constants_value_list.currentRow()
        if len(self.constants_value_list.currentItem().text()) > 0:
            self.settings.setValue(self.combos[index].currentText(), self.constants_value_list.currentItem().text())
            if len(self.constants_value_list.currentItem().text()) > 0:
                self.cw.workstation.mainq.send_bytes(
                    self.cw.workstation.encoder.encode(PybEvents.ConstantsUpdateEvent(int(self.cw.chamber_id.text()) - 1,
                                                       {self.combos[index].currentText(): self.constants_value_list.currentItem().text()})))

    def remove_option(self, option, index):
        for i, combo in enumerate(self.combos):
            if i != index:
                combo.removeItem(combo.findText(option))

    def add_option(self, option, index):
        for i, combo in enumerate(self.combos):
            if i != index:
                combo.addItem(option)

