from source.Events.GUIEventLogger import GUIEventLogger
from PyQt5.QtWidgets import *
import pkgutil
import importlib
import inspect


class ConfigurationDialog(QDialog):
    def __init__(self, cw):
        super().__init__()
        self.cw = cw

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
        for logger in cw.event_loggers:
            if not type(logger).__name__ == "TextEventLogger":
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

    def on_logger_clicked(self, _):
        self.remove_button.setDisabled(False)

    def remove_logger(self):
        del self.cw.logger_params[self.logger_list.currentRow()]
        del self.cw.event_loggers[self.logger_list.currentRow()]
        self.logger_list.takeItem(self.logger_list.currentRow())
        self.remove_button.setDisabled(False)

    def add_logger(self):
        ld = AddLoggerDialog()
        if ld.exec():
            logger_type = getattr(importlib.import_module("Events." + ld.logger.currentText()), ld.logger.currentText())
            self.cw.logger_params.append(ld.params)
            new_logger = logger_type(*ld.params)
            self.cw.event_loggers.append(new_logger)
            QListWidgetItem(ld.logger.currentText(), self.logger_list)
            if isinstance(new_logger, GUIEventLogger):
                self.cw.chamber.addWidget(new_logger.get_widget())


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
            if f.name.endswith("Logger") and not f.name == "EventLogger" and not f.name == "TextEventLogger":
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
            else:
                self.reject()
        else:
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
            if param_defaults is not None and len(self.param_names) - i <= len(param_defaults):
                param.setText(str(param_defaults[-(len(self.param_names) - i)]))
            param_box_layout.addWidget(param)
            self.layout.addWidget(param_box)
            self.params.append(param)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)
