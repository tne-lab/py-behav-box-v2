from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pkgutil
import importlib
import inspect


class SettingsDialog(QDialog):
    def __init__(self, workstation):
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
    
    def accept(self):
        settings = QSettings()
        settings.setValue("n_chamber", self.n_chamber.text())
        self.workstation.compute_chambergui()
        super(SettingsDialog, self).accept()

    def on_source_clicked(self, _):
        self.remove_button.setDisabled(False)

    def remove_source(self):
        st = self.source_list.currentItem().text()
        st_name = st.split(" (")[0]
        settings = QSettings()
        source_string = settings.value("sources")
        si = source_string.find(st_name)
        if si - 3 > 0:
            si -= 3
        else:
            si -= 1
        se = source_string.find(")", si)
        self.workstation.sources[st_name].close()
        del self.workstation.sources[st_name]
        self.source_list.takeItem(self.source_list.currentRow())
        self.remove_button.setDisabled(False)
        settings = QSettings()
        settings.setValue("sources", source_string[0:si] + source_string[se+1:])

    def add_source(self):
        self.asd = AddSourceDialog(self)
        self.asd.show()


class AddSourceDialog(QDialog):
    def __init__(self, sd):
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

    def set_params(self):
        source_type = getattr(importlib.import_module("Sources." + self.source.currentText()), self.source.currentText())
        all_params = inspect.getfullargspec(source_type.__init__)
        if len(all_params.args) > 1:
            self.spd = SourceParametersDialog(self, all_params)
            self.spd.show()
        else:
            self.accept()

    def accept(self):
        source_type = getattr(importlib.import_module("Sources." + self.source.currentText()),
                              self.source.currentText())
        settings = QSettings()
        source_string = settings.value("sources")
        source_string = source_string[:-1] + ', "{}": {}({})'.format(self.name.text(), self.source.currentText(),
                                                                     ','.join(f'"{w}"' for w in self.params)) + "}"
        settings.setValue("sources", source_string)
        self.sd.workstation.sources[self.name.text()] = source_type(*self.params)
        QListWidgetItem("{} ({})".format(self.name.text(), self.source.currentText()), self.sd.source_list)
        super(AddSourceDialog, self).accept()


class SourceParametersDialog(QDialog):
    def __init__(self, asd, all_params):
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

    def accept(self):
        for p in self.params:
            self.asd.params.append(p.text())
        super(SourceParametersDialog, self).accept()
        self.asd.accept()

    def reject(self):
        super(SourceParametersDialog, self).reject()
        self.asd.reject()
