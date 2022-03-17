import inspect
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pkgutil
import importlib


class AddLoggerDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.params = []
        self.setWindowTitle("Add Event Logger")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.set_params)
        self.control_buttons.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.logger = QComboBox()
        self.loggers = []
        for f in pkgutil.iter_modules(['Events']):
            if f.name.endswith("Logger") and not f.name == "EventLogger" and not f.name == "GUIEventLogger":
                self.loggers.append(f.name)
        self.logger.addItems(self.loggers)
        self.layout.addWidget(self.logger)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def set_params(self):
        logger_type = getattr(importlib.import_module("Events." + self.logger.currentText()), self.logger.currentText())
        all_params = inspect.getfullargspec(logger_type.__init__)
        if len(all_params.args) > 1:
            lpd = LoggerParametersDialog(self.logger.currentText(), all_params)
            if lpd.exec():
                for p in lpd.params:
                    self.params.append(p.text())
        self.accept()


class LoggerParametersDialog(QDialog):
    def __init__(self, logger, all_params):
        super().__init__()

        self.setWindowTitle(logger)

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
            if len(self.param_names) - i <= len(param_defaults):
                param.setText(str(param_defaults[-(len(self.param_names) - i)]))
            param_box_layout.addWidget(param)
            self.layout.addWidget(param_box)
            self.params.append(param)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)
