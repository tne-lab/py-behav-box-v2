import os

from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, QWidget, QCheckBox, \
    QListWidget, QListWidgetItem

from Events import PybEvents

from Events.EventWidget import EventWidget
from Workstation.ChamberWidget import ChamberWidget


class SubjectConfigWidget(EventWidget):

    def __init__(self):
        super(SubjectConfigWidget, self).__init__("subject_config")
        self.widget = QGroupBox('Subject Configuration')
        self.config_layout = QVBoxLayout(self.widget)
        self.controls_layout = QHBoxLayout(self.widget)
        self.protocol_specific = QCheckBox("Protocol Specific")
        self.remove_button = QPushButton()
        self.remove_button.setText("−")
        self.remove_button.setFixedWidth(30)
        self.remove_button.setDisabled(True)
        self.remove_button.clicked.connect(self.remove_constant)
        self.add_button = QPushButton()
        self.add_button.setText("+")
        self.add_button.setFixedWidth(30)
        self.add_button.clicked.connect(self.add_constant)
        self.controls_layout.addWidget(self.protocol_specific)
        self.controls_layout.addWidget(self.remove_button)
        self.controls_layout.addWidget(self.add_button)
        self.config_layout.addLayout(self.controls_layout)
        constants_name_box = QGroupBox('Name')
        constants_name_layout = QVBoxLayout(self.widget)
        self.constants_name_list = QListWidget()
        self.constants_name_list.itemClicked.connect(self.on_name_clicked)
        self.constants_name_list.itemDelegate().commitData.connect(self.on_commit)
        constants_name_layout.addWidget(self.constants_name_list)
        constants_name_box.setLayout(constants_name_layout)
        constants_value_box = QGroupBox('Value')
        constants_value_layout = QVBoxLayout(self.widget)
        self.constants_value_list = QListWidget()
        self.constants_value_list.itemClicked.connect(self.on_value_clicked)
        self.constants_value_list.itemDelegate().commitData.connect(self.on_commit)
        constants_value_layout.addWidget(self.constants_value_list)
        constants_value_box.setLayout(constants_value_layout)
        lists_layout = QHBoxLayout(self.widget)
        lists_layout.addWidget(constants_name_box)
        lists_layout.addWidget(constants_value_box)
        self.config_layout.addLayout(lists_layout)
        self.widget.setLayout(self.config_layout)

        self.settings = None

    def handle_event(self, event: PybEvents.PybEvent):
        super(SubjectConfigWidget, self).handle_event(event)
        if isinstance(event, PybEvents.OutputFileChangedEvent):
            self.constants_value_list.clear()
            self.constants_name_list.clear()
            self.load_keys()

    def load_keys(self):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        self.settings.beginGroup("subjectConfig/" + self.cw.task_name.currentText() + "/" + self.cw.subject.text())
        keys = self.settings.childKeys()
        constants = {}
        for key in keys:
            ql = QListWidgetItem(key, self.constants_name_list)
            ql.setFlags(ql.flags() | QtCore.Qt.ItemIsEditable)
            ql = QListWidgetItem(self.settings.value(key, ""), self.constants_value_list)
            ql.setFlags(ql.flags() | QtCore.Qt.ItemIsEditable)
            if len(self.settings.value(key, "")) > 0:
                constants[key] = self.settings.value(key, "")
        if len(constants) > 0:
            self.cw.workstation.mainq.send_bytes(
                self.cw.workstation.encoder.encode(PybEvents.ConstantsUpdateEvent(int(self.cw.chamber_id.text()) - 1, constants)))

    def set_chamber(self, cw: ChamberWidget):
        super(SubjectConfigWidget, self).set_chamber(cw)
        self.load_keys()

    def get_widget(self) -> QWidget:
        return self.widget

    def remove_constant(self):
        self.settings.remove(self.constants_name_list.currentItem().text())
        self.cw.workstation.mainq.send_bytes(
            self.cw.workstation.encoder.encode(PybEvents.ConstantRemoveEvent(int(self.cw.chamber_id.text()) - 1,
                                                                             self.constants_name_list.currentItem().text())))
        self.constants_value_list.takeItem(self.constants_value_list.currentRow())
        self.constants_name_list.takeItem(self.constants_name_list.currentRow())
        self.remove_button.setDisabled(True)

    def add_constant(self):
        ql = QListWidgetItem("", self.constants_name_list)
        ql.setFlags(ql.flags() | QtCore.Qt.ItemIsEditable)
        ql = QListWidgetItem("", self.constants_value_list)
        ql.setFlags(ql.flags() | QtCore.Qt.ItemIsEditable)

    def on_value_clicked(self, _):
        self.constants_name_list.setCurrentRow(self.constants_value_list.currentRow())
        self.remove_button.setDisabled(False)

    def on_name_clicked(self, _):
        self.constants_value_list.setCurrentRow(self.constants_name_list.currentRow())
        self.remove_button.setDisabled(False)

    def on_commit(self):
        if len(self.cw.task_name.currentText()) > 0:
            self.settings.setValue(self.constants_name_list.currentItem().text(), self.constants_value_list.currentItem().text())
            if len(self.constants_value_list.currentItem().text()) > 0:
                self.cw.workstation.mainq.send_bytes(
                    self.cw.workstation.encoder.encode(PybEvents.ConstantsUpdateEvent(int(self.cw.chamber_id.text()) - 1,
                                                       {self.constants_name_list.currentItem().text(): self.constants_value_list.currentItem().text()})))
