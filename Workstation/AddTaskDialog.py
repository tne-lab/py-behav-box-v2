from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pkgutil
import os


class AddTaskDialog(QDialog):
    def __init__(self, workstation):
        super().__init__()

        self.setWindowTitle("Add Task")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        load_configuration = QPushButton("Load Configuration")
        load_configuration.clicked.connect(self.load_config)
        self.control_buttons.addButton(load_configuration, QDialogButtonBox.ActionRole)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)
        self.configuration_path = None

        self.layout = QVBoxLayout()
        chamber_box = QGroupBox('Chamber')
        chamber_box_layout = QHBoxLayout(self)
        chamber_box.setLayout(chamber_box_layout)
        self.chamber = QComboBox()
        chambers = map(str, list(range(1, workstation.n_chamber + 1)))
        self.chamber.addItems(chambers)
        chamber_box_layout.addWidget(self.chamber)
        task_box = QGroupBox('Task')
        task_box_layout = QHBoxLayout(self)
        task_box.setLayout(task_box_layout)
        self.task = QComboBox()
        self.tasks = []
        for f in pkgutil.iter_modules(['Tasks']):
            if not f.name == "Task":
                self.tasks.append(f.name)
        self.task.addItems(self.tasks)
        task_box_layout.addWidget(self.task)
        self.layout.addWidget(task_box)
        self.layout.addWidget(chamber_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)

    def load_config(self):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        file_name = QFileDialog.getOpenFileName(self, 'Select File',
                                                "{}/py-behav/Configurations/".format(desktop),
                                                '*.csv')
        if len(file_name[0]) > 1:
            self.configuration_path = file_name[0]
            self.accept()
