from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pkgutil


class AddTaskDialog(QDialog):
    def __init__(self, workstation):
        super().__init__()

        self.setWindowTitle("Add Task")

        control = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.control_buttons = QDialogButtonBox(control)
        self.control_buttons.accepted.connect(self.accept)
        self.control_buttons.rejected.connect(self.reject)

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
        tasks = []
        for f in pkgutil.iter_modules(['Tasks']):
            if not f.name == "Task":
                tasks.append(f.name)
        self.task.addItems(tasks)
        task_box_layout.addWidget(self.task)
        self.layout.addWidget(task_box)
        self.layout.addWidget(chamber_box)
        self.layout.addWidget(self.control_buttons)
        self.setLayout(self.layout)
