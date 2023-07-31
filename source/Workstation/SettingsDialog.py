from __future__ import annotations

import multiprocessing
import os
from typing import TYPE_CHECKING

from Utilities.create_task import create_task
from Utilities.find_closing_paren import find_closing_paren

if TYPE_CHECKING:
    from Workstation.Workstation import Workstation

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pkgutil
import importlib
import inspect


class SettingsDialog(QDialog):
    def __init__(self, workstation: Workstation):
        super().__init__()
        self.asd = None
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
        refresh_box = QGroupBox('GUI Options')
        refresh_box_layout = QHBoxLayout(self)
        refresh_box.setLayout(refresh_box_layout)
        self.refresh_gui = QCheckBox("Refresh")
        self.refresh_gui.setChecked(self.workstation.refresh_gui)
        self.refresh_gui.stateChanged.connect(self.update_refresh_check)
        refresh_box_layout.addWidget(self.refresh_gui)
        self.layout.addWidget(refresh_box)
        source_box = QGroupBox('Sources')
        source_box_layout = QVBoxLayout(self)
        self.source_list = QListWidget()
        for sn in workstation.sources:
            ql = QListWidgetItem("{} ({})".format(sn, type(workstation.sources[sn]).__name__), self.source_list)
            if workstation.sources[sn].available:
                ql.setIcon(self.source_list.style().standardIcon(QStyle.SP_DialogApplyButton))
            else:
                ql.setIcon(self.source_list.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.source_list.itemClicked.connect(self.on_source_clicked)
        source_box_layout.addWidget(self.source_list)
        source_as_layout = QHBoxLayout(self)
        source_as_layout.addStretch()
        self.refresh_button = QPushButton()
        self.refresh_button.setText("⟳")
        self.refresh_button.setFixedWidth(30)
        self.refresh_button.setDisabled(True)
        self.refresh_button.clicked.connect(lambda: create_task(self.refresh_source()))
        source_as_layout.addWidget(self.refresh_button)
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

    def update_refresh_check(self):
        self.workstation.refresh_gui = self.refresh_gui.isChecked()
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        settings.setValue("refresh_gui", self.workstation.refresh_gui)
    
    def accept(self) -> None:
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        settings.setValue("n_chamber", self.n_chamber.text())
        self.workstation.n_chamber = int(self.n_chamber.text())
        self.workstation.compute_chambergui()
        super(SettingsDialog, self).accept()

    def on_source_clicked(self, _) -> None:
        self.remove_button.setDisabled(False)
        self.refresh_button.setDisabled(False)

    def refresh_source(self) -> None:
        st = self.source_list.currentItem().text()
        st_name = st.split(" (")[0]
        if len(self.workstation.sources[st_name].components) == 0:
            desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
            settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
            source_string = settings.value("sources")
            s_type = type(self.workstation.sources[st_name]).__name__
            search_str = '\"'+st_name+'\": ' + s_type
            open_ind = source_string.index(search_str) + len(search_str)
            close_ind = find_closing_paren(source_string, open_ind) + 1
            source_module = importlib.import_module("Sources." + s_type)
            attribute = getattr(source_module, s_type)
            globals()[s_type] = attribute
            self.workstation.sources[st_name] = eval(type(self.workstation.sources[st_name]).__name__ + source_string[open_ind:close_ind])
            if self.workstation.sources[st_name].is_available():
                self.source_list.currentItem().setIcon(self.source_list.style().standardIcon(QStyle.SP_DialogApplyButton))
            else:
                self.source_list.currentItem().setIcon(self.source_list.style().standardIcon(QStyle.SP_DialogCancelButton))

    def remove_source(self) -> None:
        st = self.source_list.currentItem().text()
        st_name = st.split(" (")[0]
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        source_string = settings.value("sources")
        si = source_string.find(st_name)
        if si - 3 > 0:
            si -= 3
        else:
            si -= 1
        se = source_string.find(")", si)
        self.workstation.sources[st_name].close_source()
        del self.workstation.sources[st_name]
        self.source_list.takeItem(self.source_list.currentRow())
        self.remove_button.setDisabled(False)
        settings.setValue("sources", source_string[0:si] + source_string[se+1:])

    def add_source(self) -> None:
        self.asd = AddSourceDialog(self)
        self.asd.show()


class AddSourceDialog(QDialog):
    def __init__(self, sd: SettingsDialog):
        super(AddSourceDialog, self).__init__()
        self.sd = sd
        self.spd = None
        self.setWindowTitle("Add Source")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.set_params)
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
        self.params = []

    def set_params(self) -> None:
        source_type = getattr(importlib.import_module("Sources." + self.source.currentText()), self.source.currentText())
        all_params = inspect.getfullargspec(source_type.__init__)
        if len(all_params.args) > 1:
            self.spd = SourceParametersDialog(self, all_params)
            self.spd.show()
        else:
            self.accept()

    def accept(self) -> None:
        source_type = getattr(importlib.import_module("Sources." + self.source.currentText()),
                              self.source.currentText())
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        source_string = settings.value("sources")
        if source_string == '{}':
            source_string = "{" + '"{}": \'{}({})\''.format(self.name.text(), self.source.currentText(),
                                                          ','.join(f'"{w}"' for w in self.params)) + "}"
        else:
            source_string = source_string[:-1] + ', "{}": "\'{}({})"'.format(self.name.text(), self.source.currentText(),
                                                                           ','.join(f'"{w}"' for w in self.params)) + "\'}"
        settings.setValue("sources", source_string)
        self.sd.workstation.sources[self.name.text()] = source_type(*self.params)
        tpq, sourceq = multiprocessing.Pipe()
        self.sd.workstation.sources[self.name.text()].queue = sourceq
        self.sd.workstation.sources[self.name.text()].start()
        ql = QListWidgetItem("{} ({})".format(self.name.text(), self.source.currentText()), self.sd.source_list)
        if self.sd.workstation.sources[self.name.text()].is_available():
            ql.setIcon(self.sd.source_list.style().standardIcon(QStyle.SP_DialogApplyButton))
        else:
            ql.setIcon(self.sd.source_list.style().standardIcon(QStyle.SP_DialogCancelButton))
        super(AddSourceDialog, self).accept()


class SourceParametersDialog(QDialog):
    def __init__(self, asd: AddSourceDialog, all_params: inspect.FullArgSpec):
        super().__init__()
        self.asd = asd

        self.setWindowTitle("{} ({})".format(self.asd.name, self.asd.source.currentText()))

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

    def accept(self) -> None:
        for p in self.params:
            self.asd.params.append(p.text())
        super(SourceParametersDialog, self).accept()
        self.asd.accept()

    def reject(self) -> None:
        super(SourceParametersDialog, self).reject()
        self.asd.reject()
