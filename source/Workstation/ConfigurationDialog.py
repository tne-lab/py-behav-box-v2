from Events.GUIEventLogger import GUIEventLogger
from PyQt5.QtWidgets import *
import pkgutil
import importlib
import inspect


class ConfigurationDialog(QDialog):
    def __init__(self, cw):
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
        self.logger_inds = []
        for i, logger in enumerate(cw.event_loggers):
            if not type(logger).__name__ == "TextEventLogger":
                self.logger_inds.append(i)
                QListWidgetItem(type(logger).__name__, self.logger_list)
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
        self.add_button.clicked.connect(self.add_logger)  # Make function
        logger_as_layout.addWidget(self.add_button)
        logger_box_layout.addLayout(logger_as_layout)
        logger_box.setLayout(logger_box_layout)
        self.layout.addWidget(logger_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)
    
    def accept(self):
        self.cw.prompt = self.prompt.text()  # Update the prompt from the configuration
        self.cw.refresh()
        super(ConfigurationDialog, self).accept()

    def on_logger_clicked(self, _):
        self.remove_button.setDisabled(False)

    def remove_logger(self):
        ind = self.logger_inds[self.logger_list.currentRow()]
        if isinstance(self.cw.event_loggers[ind], GUIEventLogger):
            self.cw.chamber.removeWidget(self.cw.event_loggers[ind].get_widget())
            self.cw.event_loggers[ind].get_widget().deleteLater()
        del self.cw.logger_params[self.logger_list.currentRow()]
        del self.cw.event_loggers[ind]
        self.logger_list.takeItem(self.logger_list.currentRow())
        self.remove_button.setDisabled(False)

    def add_logger(self):
        self.ld = AddLoggerDialog(self)
        self.ld.show()


class AddLoggerDialog(QDialog):
    def __init__(self, cd):
        super().__init__()
        self.cd = cd
        self.lpd = None
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
            if f.name.endswith("Logger") and not f.name == "EventLogger" and not f.name == "TextEventLogger" and not f.name == "FileEventLogger" and not f.name == "GUIEventLogger":
                self.loggers.append(f.name)
        self.logger.addItems(self.loggers)
        self.layout.addWidget(self.logger)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def accept(self):
        logger_type = getattr(importlib.import_module("Events." + self.logger.currentText()), self.logger.currentText())
        self.cd.cw.logger_params.append(self.params)
        new_logger = logger_type(*self.params)
        self.cd.cw.event_loggers.append(new_logger)
        self.cd.logger_inds.append(len(self.cd.cw.event_loggers) - 1)
        QListWidgetItem(self.logger.currentText(), self.cd.logger_list)
        if isinstance(new_logger, GUIEventLogger):
            new_logger.set_chamber(self.cd.cw)
            self.cd.cw.chamber.addWidget(new_logger.get_widget())
        super(AddLoggerDialog, self).accept()

    def set_params(self):
        logger_type = getattr(importlib.import_module("Events." + self.logger.currentText()), self.logger.currentText())
        all_params = inspect.getfullargspec(logger_type.__init__)
        if len(all_params.args) > 1:
            self.lpd = LoggerParametersDialog(self, all_params)
            self.lpd.show()
        else:
            self.accept()


class LoggerParametersDialog(QDialog):
    def __init__(self, ald, all_params):
        super().__init__()
        self.ald = ald
        self.setWindowTitle(ald.logger.currentText())

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
            self.ald.params.append(p.text())
        super(LoggerParametersDialog, self).accept()
        self.ald.accept()

    def reject(self):
        super(LoggerParametersDialog, self).reject()
        self.ald.reject()
