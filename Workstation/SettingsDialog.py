from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pkgutil
import os
import importlib
import inspect


class SettingsDialog(QDialog):
    def __init__(self, workstation):
        super().__init__()
        self.workstation = workstation

        self.setWindowTitle("Settings")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)
        self.configuration_path = None

        self.layout = QVBoxLayout()
        chamber_box = QGroupBox('Chamber Count')
        chamber_box_layout = QHBoxLayout(self)
        chamber_box.setLayout(chamber_box_layout)
        self.n_chamber = QLineEdit(str(workstation.n_chamber))
        chamber_box_layout.addWidget(self.n_chamber)
        self.layout.addWidget(chamber_box)
        source_box = QGroupBox('Sources')
        source_box_layout = QVBoxLayout(self)
        self.source_list = QListWidget()
        for sn in workstation.sources:
            QListWidgetItem("{} ({})".format(sn, type(workstation.sources[sn]).__name__), self.source_list)
        self.source_list.itemClicked.connect(self.on_source_clicked)
        source_box_layout.addWidget(self.source_list)
        source_as_layout = QHBoxLayout(self)
        source_as_layout.addStretch()
        self.remove_button = QPushButton()
        self.remove_button.setText("−")
        self.remove_button.setFixedWidth(30)
        self.remove_button.setDisabled(True)
        self.remove_button.clicked.connect(self.remove_source)
        source_as_layout.addWidget(self.remove_button)
        self.add_button = QPushButton()
        self.add_button.setText("+")
        self.add_button.setFixedWidth(30)
        self.add_button.clicked.connect(self.add_source)
        source_as_layout.addWidget(self.add_button)
        source_box_layout.addLayout(source_as_layout)
        source_box.setLayout(source_box_layout)
        self.layout.addWidget(source_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def on_source_clicked(self, _):
        self.remove_button.setDisabled(False)

    def remove_source(self):
        st = self.source_list.currentItem().text()
        st_name = st.split(" (")[0]
        settings = QSettings()
        source_string = settings.value("sources")
        print(source_string)
        si = source_string.find(st_name)
        if si - 3 > 0:
            si -= 3
        else:
            si -= 1
        se = source_string.find(")", si)
        print("{} {}".format(si, se))
        del self.workstation.sources[st_name]
        self.source_list.takeItem(self.source_list.currentRow())
        self.remove_button.setDisabled(False)

    def add_source(self):
        sd = AddSourceDialog()
        if sd.exec():
            source_type = getattr(importlib.import_module("Sources." + sd.source.currentText()), sd.source.currentText())
            all_params = inspect.getfullargspec(source_type.__init__)
            params = []
            if len(all_params.args) > 1:
                spd = SourceParametersDialog(sd.name.text(), sd.source.currentText(), all_params)
                if spd.exec():
                    for p in spd.params:
                        params.append(p.text())
            settings = QSettings()
            source_string = settings.value("sources")
            source_string = source_string[:-1] + ', "{}": {}({})'.format(sd.name.text(), sd.source.currentText(), ''.join(f'"{w}"' for w in params)) + "}"
            settings.setValue("sources", source_string)
            self.workstation.sources[sd.name.text()] = source_type(*params)
            QListWidgetItem("{} ({})".format(sd.name.text(), sd.source.currentText()), self.source_list)



class AddSourceDialog(QDialog):
    def __init__(self):
        super(AddSourceDialog, self).__init__()
        self.setWindowTitle("Add Source")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)
        self.configuration_path = None

        self.layout = QVBoxLayout()
        name_box = QGroupBox('Name')
        name_box_layout = QHBoxLayout(self)
        name_box.setLayout(name_box_layout)
        self.name = QLineEdit()
        name_box_layout.addWidget(self.name)
        self.layout.addWidget(name_box)
        source_box = QGroupBox('Source')
        source_box_layout = QHBoxLayout(self)
        source_box.setLayout(source_box_layout)
        self.source = QComboBox()
        self.sources = []
        for f in pkgutil.iter_modules(['Sources']):
            if not f.name == "Source":
                self.sources.append(f.name)
        self.source.addItems(self.sources)
        source_box_layout.addWidget(self.source)
        self.layout.addWidget(source_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)


class SourceParametersDialog(QDialog):
    def __init__(self, name, source_type, all_params):
        super().__init__()

        self.setWindowTitle("{} ({})".format(name, source_type))

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)
        self.layout = QVBoxLayout()

        self.param_names = all_params.args
        param_defaults = all_params.defaults
        self.params = []
        for i in range(1, len(self.param_names)):
            param_box = QGroupBox(self.param_names[i])
            param_box_layout = QHBoxLayout(self)
            param_box.setLayout(param_box_layout)
            param = QLineEdit()
            if param_defaults is not None and len(self.param_names) - i <= len(param_defaults):
                param.setText(str(param_defaults[-(len(self.param_names) - i)]))
            param_box_layout.addWidget(param)
            self.layout.addWidget(param_box)
            self.params.append(param)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)
