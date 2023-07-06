from __future__ import annotations

from typing import TYPE_CHECKING

from Events.TerminalWidget import TerminalWidget

if TYPE_CHECKING:
    from Workstation.WorkstationGUI import WorkstationGUI

import csv
import importlib
import re

from PyQt5.QtWidgets import *
import pkgutil
import os


class AddTaskDialog(QDialog):
    def __init__(self, wsg: WorkstationGUI):
        super().__init__()

        self.fd = None
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
        for f in pkgutil.iter_modules(['Local/Tasks']):
            self.tasks.append(f.name)
        self.task.addItems(self.tasks)
        task_box_layout.addWidget(self.task)
        self.layout.addWidget(task_box)
        self.layout.addWidget(chamber_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def accept(self) -> None:
        if self.configuration_path is not None:  # If a configuration file was provided
            with open(self.configuration_path, newline='') as csvfile:  # Open the configuration file
                config_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                # Default task values
                chamber = 0
                event_loggers = task = subject = afp = pfp = ""
                widgets = []
                widget_params = []
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
                        event_loggers = row[1]
                    elif row[0] == "Widgets":
                        types = list(
                            map(lambda x: x.split("))")[-1],
                                row[1].split("((")))  # Get the type of each widget
                        params = list(
                            map(lambda x: x.split("((")[-1],
                                row[1].split("))")))  # Get the parameters for each widget
                        for i in range(len(types) - 1):
                            logger_type = getattr(importlib.import_module("Events." + types[i]),
                                                  types[i])  # Import the logger
                            param_vals = re.findall("\|\|(.+?)\|\|", params[i])  # Extract the parameters
                            widgets.append(logger_type(*param_vals))  # Instantiate the widget
                            widget_params.append(param_vals)

                self.wsg.add_task(chamber, task, subject, afp, pfp, prompt, event_loggers)
        else:
            self.wsg.add_task(self.chamber.currentText(), self.task.currentIndex(), event_loggers="CSVEventLogger((||file_log||))", widgets=[TerminalWidget("gui_log")], widget_params=[["gui_log"]])
        super(AddTaskDialog, self).accept()

    def load_config(self) -> None:
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.fd = QFileDialog(self)
        self.fd.setFileMode(QFileDialog.ExistingFile)
        self.fd.setViewMode(QFileDialog.List)
        self.fd.setNameFilter("CSV files (*.csv)")
        self.fd.setDirectory("{}/py-behav/Configurations/".format(desktop))
        self.fd.setWindowTitle('Select File')
        self.fd.accept = self.open_file
        self.fd.show()

    def open_file(self):
        if len(self.fd.selectedFiles()[0]) > 1:
            self.configuration_path = self.fd.selectedFiles()[0]
            super(QFileDialog, self.fd).accept()
            self.accept()
