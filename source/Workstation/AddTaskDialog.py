import csv
import importlib
from typing import re

from PyQt5.QtWidgets import *
import pkgutil
import os


class AddTaskDialog(QDialog):
    def __init__(self, wsg):
        super().__init__()

        self.wsg = wsg
        self.setWindowTitle("Add Task")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)

        load_configuration = QPushButton("Load Configuration")
        load_configuration.clicked.connect(self.load_config)
        self.control_buttons.addButton(load_configuration, QDialogButtonBox.ActionRole)
        self.configuration_path = None

        self.layout = QVBoxLayout()
        chamber_box = QGroupBox('Chamber')
        chamber_box_layout = QHBoxLayout(self)
        chamber_box.setLayout(chamber_box_layout)
        self.chamber = QComboBox()
        chambers = map(str, list(range(1, self.wsg.workstation.n_chamber + 1)))
        self.chamber.addItems(chambers)
        chamber_box_layout.addWidget(self.chamber)
        task_box = QGroupBox('Task')
        task_box_layout = QHBoxLayout(self)
        task_box.setLayout(task_box_layout)
        self.task = QComboBox()
        self.tasks = []
        for f in pkgutil.iter_modules(['Tasks']):
            if not f.name == "Task" and not f.name == "TaskSequence":
                self.tasks.append(f.name)
        self.task.addItems(self.tasks)
        task_box_layout.addWidget(self.task)
        self.layout.addWidget(task_box)
        self.layout.addWidget(chamber_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def accept(self):
        if self.configuration_path is not None:  # If a configuration file was provided
            with open(self.configuration_path, newline='') as csvfile:  # Open the configuration file
                config_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                # Default task values
                chamber = task = subject = afp = pfp = ""
                event_loggers = []
                logger_params = []
                # Check for each relevant row in the configuration
                for row in config_reader:
                    if row[0] == "Chamber":
                        chamber = row[1]
                    elif row[0] == "Subject":
                        subject = row[1]
                    elif row[0] == "Task":
                        task = self.tasks.index(row[1])
                    elif row[0] == "Address File":
                        afp = row[1]
                    elif row[0] == "Protocol":
                        pfp = row[1]
                    elif row[0] == "Prompt":
                        prompt = row[1]
                    elif row[0] == "EventLoggers":
                        types = list(
                            map(lambda x: x.split("))")[-1], row[1].split("((")))  # Get the type of each logger
                        params = list(
                            map(lambda x: x.split("((")[-1], row[1].split("))")))  # Get the parameters for each logger
                        for i in range(len(types) - 1):
                            logger_type = getattr(importlib.import_module("Events." + types[i]),
                                                  types[i])  # Import the logger
                            param_vals = re.findall("\|\|(.+?)\|\|", params[i])  # Extract the parameters
                            event_loggers.append(logger_type(*param_vals))  # Instantiate the logger
                            logger_params.append(param_vals)

                self.wsg.add_task(chamber, task, subject, afp, pfp, prompt, (event_loggers, logger_params))
        else:
            self.wsg.add_task(self.chamber.currentText(), self.task.currentIndex())
        super(AddTaskDialog, self).accept()

    def load_config(self):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        file_name = QFileDialog.getOpenFileName(self, 'Select File',
                                                "{}/py-behav/Configurations/".format(desktop),
                                                '*.csv')
        if len(file_name[0]) > 1:
            self.configuration_path = file_name[0]
            self.accept()
