from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pybehave.Events.PybEvents import AddLoggerEvent, RemoveLoggerEvent
import pybehave.Events
from pybehave.Utilities.Exceptions import MissingExtraError

if TYPE_CHECKING:
    from pybehave.Workstation.ChamberWidget import ChamberWidget

from PyQt5.QtWidgets import *
import pkgutil
import importlib
import inspect


class ConfigurationDialog(QDialog):
    def __init__(self, cw: ChamberWidget):
        super().__init__()
        self.cw = cw
        self.ld = None

        self.setWindowTitle("Settings")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)
        self.configuration_path = None

        self.layout = QVBoxLayout()
        prompt_box = QGroupBox('Prompt')
        prompt_box_layout = QHBoxLayout(self)
        prompt_box.setLayout(prompt_box_layout)
        self.prompt = QLineEdit(cw.prompt)  # Correct default
        prompt_box_layout.addWidget(self.prompt)
        self.layout.addWidget(prompt_box)
        logger_box = QGroupBox('Event Loggers')
        logger_box_layout = QVBoxLayout(self)
        self.logger_list = QListWidget()
        loggers = list(map(lambda x: x.split("))")[-1], self.cw.event_loggers.split("((")))
        params = list(map(lambda x: x.split("((")[-1], self.cw.event_loggers.split("))")))
        for i in range(len(loggers)):
            if len(loggers[i]) > 0:
                param_vals = re.findall("\|\|(.+?)\|\|", params[i])
                QListWidgetItem("{} ({})".format(param_vals[0], loggers[i]), self.logger_list)
        self.logger_list.itemClicked.connect(self.on_logger_clicked)
        logger_box_layout.addWidget(self.logger_list)
        logger_as_layout = QHBoxLayout(self)
        logger_as_layout.addStretch()
        self.remove_button = QPushButton()
        self.remove_button.setText("−")
        self.remove_button.setFixedWidth(30)
        self.remove_button.setDisabled(True)
        self.remove_button.clicked.connect(self.remove_logger)  # Make function
        logger_as_layout.addWidget(self.remove_button)
        self.add_button = QPushButton()
        self.add_button.setText("+")
        self.add_button.setFixedWidth(30)
        self.add_button.clicked.connect(lambda: self.add_extra(True))  # Make function
        logger_as_layout.addWidget(self.add_button)
        logger_box_layout.addLayout(logger_as_layout)
        logger_box.setLayout(logger_box_layout)
        self.layout.addWidget(logger_box)

        widget_box = QGroupBox('Widgets')
        widget_box_layout = QVBoxLayout(self)
        self.widget_list = QListWidget()
        for widget in self.cw.widgets:
            QListWidgetItem("{} ({})".format(widget.name, type(widget).__name__), self.widget_list)
        self.widget_list.itemClicked.connect(self.on_widget_clicked)
        widget_box_layout.addWidget(self.widget_list)
        widget_as_layout = QHBoxLayout(self)
        widget_as_layout.addStretch()
        self.remove_widget_button = QPushButton()
        self.remove_widget_button.setText("−")
        self.remove_widget_button.setFixedWidth(30)
        self.remove_widget_button.setDisabled(True)
        self.remove_widget_button.clicked.connect(self.remove_widget)  # Make function
        widget_as_layout.addWidget(self.remove_widget_button)
        self.add_widget_button = QPushButton()
        self.add_widget_button.setText("+")
        self.add_widget_button.setFixedWidth(30)
        self.add_widget_button.clicked.connect(lambda: self.add_extra(False))  # Make function
        widget_as_layout.addWidget(self.add_widget_button)
        widget_box_layout.addLayout(widget_as_layout)
        widget_box.setLayout(widget_box_layout)
        self.layout.addWidget(widget_box)

        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)
        self.error_dialog = None
    
    def accept(self) -> None:
        self.cw.prompt = self.prompt.text()  # Update the prompt from the configuration
        super(ConfigurationDialog, self).accept()

    def on_logger_clicked(self, _) -> None:
        self.remove_button.setDisabled(False)

    def on_widget_clicked(self, _) -> None:
        self.remove_widget_button.setDisabled(False)

    def remove_widget(self) -> None:
        self.cw.chamber.removeWidget(self.cw.widgets[self.widget_list.currentRow()].get_widget())
        self.cw.widgets[self.widget_list.currentRow()].get_widget().deleteLater()
        del self.cw.widgets[self.widget_list.currentRow()]
        del self.cw.widget_params[self.widget_list.currentRow()]
        self.widget_list.takeItem(self.widget_list.currentRow())
        self.remove_button.setDisabled(False)

    def remove_logger(self) -> None:
        txt = self.cw.event_loggers.split('))')
        params = txt[self.logger_list.currentRow()].split('((')[1]
        param_vals = re.findall("\|\|(.+?)\|\|", params)
        del txt[self.logger_list.currentRow()]
        self.cw.event_loggers = '))'.join(txt)
        self.logger_list.takeItem(self.logger_list.currentRow())
        self.remove_button.setDisabled(False)
        self.cw.workstation.mainq.send_bytes(self.cw.workstation.encoder.encode(RemoveLoggerEvent(int(self.cw.chamber_id.text()) - 1, param_vals[0])))

    def add_extra(self, logger=True) -> None:
        self.ld = AddExtrasDialog(self, logger)
        self.ld.show()


class AddExtrasDialog(QDialog):
    def __init__(self, cd: ConfigurationDialog, logger=True):
        super().__init__()
        self.cd = cd
        self.epd = None
        self.params = []
        self.logger = logger
        self.setWindowTitle("Add Event Logger" if logger else "Add Widget")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.set_params)
        self.control_buttons.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.extra = QComboBox()
        self.extras = []
        for f in pkgutil.iter_modules(pybehave.Events.__path__):
            if logger and f.name.endswith("Logger") and not f.name == "EventLogger" and not f.name == "FileEventLogger":
                self.extras.append(f.name)
            elif not logger and f.name.endswith("Widget") and not f.name == "Widget" and not f.name == "EventWidget":
                self.extras.append(f.name)
        self.extra.addItems(self.extras)
        self.layout.addWidget(self.extra)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def accept(self) -> None:
        if not self.logger:
            widget_type = getattr(importlib.import_module("pybehave.Events." + self.extra.currentText()), self.extra.currentText())
            new_widget = widget_type(*self.params)
            self.cd.cw.widgets.append(new_widget)
            self.cd.cw.widget_params.append(self.params)
            new_widget.set_chamber(self.cd.cw)
            self.cd.cw.chamber.addWidget(new_widget)
            QListWidgetItem("{} ({})".format(new_widget.name, self.extra.currentText()), self.cd.widget_list)
        else:
            logger_text = self.extra.currentText() + "((" + ''.join(f"||{w}||" for w in self.params) + "))"
            self.cd.cw.event_loggers += logger_text
            QListWidgetItem("{} ({})".format(self.params[0], self.extra.currentText()), self.cd.logger_list)
            self.cd.cw.workstation.mainq.send_bytes(self.cd.cw.workstation.encoder.encode(AddLoggerEvent(int(self.cd.cw.chamber_id.text()) - 1, logger_text)))
            self.cd.cw.output_file_changed()
        super(AddExtrasDialog, self).accept()

    def set_params(self) -> None:
        try:
            logger_type = getattr(importlib.import_module("pybehave.Events." + self.extra.currentText()), self.extra.currentText())
            all_params = inspect.getfullargspec(logger_type.__init__)
            if len(all_params.args) > 1:
                self.epd = ExtrasParametersDialog(self, all_params)
                self.epd.show()
            else:
                self.accept()
        except MissingExtraError as e:
            self.cd.error_dialog = QMessageBox(self)
            self.cd.error_dialog.setWindowTitle('Missing extra')
            self.cd.error_dialog.setText(f'{self.extra.currentText()} requires the \'{e.extra}\' extra. This extra can be installed by running \'pip install pybehave[{e.extra}]\' (or \'pip install .[{e.extra}]\' if you\'re using a local installation) in your pybehave virtual environment.')
            self.cd.error_dialog.setStandardButtons(QMessageBox.Ok)
            self.cd.error_dialog.setIcon(QMessageBox.Critical)
            self.cd.error_dialog.show()
            self.close()


class ExtrasParametersDialog(QDialog):
    def __init__(self, aed: AddExtrasDialog, all_params: inspect.FullArgSpec):
        super().__init__()
        self.aed = aed
        self.setWindowTitle(aed.extra.currentText())

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
            self.aed.params.append(p.text())
        super(ExtrasParametersDialog, self).accept()
        self.aed.accept()

    def reject(self) -> None:
        super(ExtrasParametersDialog, self).reject()
        self.aed.reject()
