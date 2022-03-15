from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
from Workstation.AddTaskDialog import AddTaskDialog
from Workstation.ChamberWidget import ChamberWidget


class WorkstationGUI(QWidget):
    def __init__(self, workstation, szo):
        QWidget.__init__(self)
        self.n_active = 0
        self.workstation = workstation

        self.setWindowTitle("Pybehav")
        self.setGeometry(0, 0, int(szo[0] / 6), int(szo[1] - 70))
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        menubar = QMenuBar()
        main_layout.addWidget(menubar)
        action_file = menubar.addMenu("File")
        add_task = action_file.addAction("Add Task")
        add_task.triggered.connect(self.task_dialog)
        action_file.addAction("Load Configuration")
        action_file.addAction("Save Configuration")
        action_file.addSeparator()
        action_file.addAction("Quit")
        menubar.addMenu("View")
        menubar.addMenu("Help")

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)

        self.chamber_container = QVBoxLayout(scroll_widget)
        self.chambers = {}
        self.chamber_container.addStretch(1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.workstation.loop)
        self.timer.setInterval(1)
        self.timer.start()

        self.setLayout(self.chamber_container)
        self.move(0, 0)
        self.show()

    def task_dialog(self):
        td = AddTaskDialog(self.workstation)
        if td.exec():
            self.add_task(td.chamber.currentText(), td.task.currentIndex())

    def add_task(self, chamber_index, task_index):
        self.chambers[int(chamber_index) - 1] = ChamberWidget(self.workstation, chamber_index, task_index)
        self.chamber_container.insertWidget(self.n_active, self.chambers[int(chamber_index) - 1])
        self.n_active += 1
