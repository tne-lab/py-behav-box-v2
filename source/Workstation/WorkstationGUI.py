from __future__ import annotations
from typing import TYPE_CHECKING

from Utilities.Exceptions import AddTaskError

if TYPE_CHECKING:
    from Events.EventLogger import EventLogger
    from Workstation.Workstation import Workstation

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from Events.CSVEventLogger import CSVEventLogger
from Workstation.AddTaskDialog import AddTaskDialog
from Workstation.SettingsDialog import SettingsDialog
from Workstation.ChamberWidget import ChamberWidget


class WorkstationGUI(QWidget):
    def __init__(self, workstation: Workstation):
        QWidget.__init__(self)
        self.sd = None
        self.td = None
        self.emsg = None
        self.n_active = 0
        self.workstation = workstation
        settings = QSettings()

        self.setWindowTitle("Pybehav")
        self.setGeometry(0, 0, int(settings.value("pyqt/w")), int(settings.value("pyqt/h")))  # Position GUI
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove GUI margins so it is flush with screen
        # Make the GUI background white
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        # Main menu bar
        menubar = QMenuBar()
        main_layout.addWidget(menubar)
        action_file = menubar.addMenu("File")  # File section of menu
        add_task = action_file.addAction("Add Task")  # Action for adding a new task to a chamber
        add_task.triggered.connect(self.task_dialog)  # Call task_dialog method when clicked
        settings = action_file.addAction("Settings")  # Action for adjusting py-behav settings
        settings.triggered.connect(self.settings_dialog)  # Call settings_dialog method when clicked
        action_file.addSeparator()
        action_file.addAction("Quit")  # Quits py-behav
        menubar.addMenu("View")
        menubar.addMenu("Help")

        # Sets up the scrolling chamber list UI
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)

        # Widget containing all the chambers
        self.chamber_container = QVBoxLayout(scroll_widget)
        self.chambers = {}
        self.chamber_container.addStretch(1)

        self.setLayout(self.chamber_container)
        self.move(0, 0)
        self.show()

    def settings_dialog(self) -> None:
        # Opens the SettingsDialog for adjusting py-behav settings
        self.sd = SettingsDialog(self.workstation)
        self.sd.show()

    def task_dialog(self) -> None:
        # Opens the AddTaskDialog for adding a new task to a chamber
        self.td = AddTaskDialog(self)
        self.td.show()

    def add_task(self, chamber_index: int, task_index: int, subject: str = "default", afp: str = "", pfp: str = "", prompt: str = "", event_loggers: tuple[list[EventLogger], list[list[str]]] = None) -> None:
        """
        Adds a ChamberWidget to the GUI corresponding to a new task

        Parameters
        ----------
        chamber_index : str
            The index of the chamber the task is being added to
        task_index : int
            The index of the task in the list of possible tasks
        subject : str
            The name of the subject
        afp : str
            The path to the address file
        pfp : str
            The path to the protocol file
        prompt : str
            Message to display before task starts
        event_loggers : list
            The EventLoggers used by this task
        """
        if int(chamber_index) - 1 not in self.chambers:
            if event_loggers is None:
                event_loggers = ([CSVEventLogger()], [[]])
            try:
                self.chambers[int(chamber_index) - 1] = ChamberWidget(self, chamber_index, task_index, subject, afp, pfp, prompt, event_loggers)
                self.chamber_container.insertWidget(self.n_active, self.chambers[int(chamber_index) - 1])
            except AddTaskError:
                self.remove_task(int(chamber_index) - 1)
            self.n_active += 1  # Increment the number of active chambers
        else:  # The chamber is already in use
            self.emsg = QMessageBox()
            self.emsg.setIcon(QMessageBox.Critical)
            self.emsg.setText('Chamber already occupied, clear before adding a new task')
            self.emsg.setWindowTitle("Error")
            self.emsg.show()

    def remove_task(self, chamber_index: int) -> None:
        """
        Removes a task

        Parameters
        ----------
        chamber_index : str
            The index of the task
        """
        self.workstation.remove_task(int(chamber_index) - 1)  # Remove the task from the main Workstation
        if int(chamber_index) - 1 in self.chambers:
            self.chamber_container.removeWidget(self.chambers[int(chamber_index) - 1])  # Remove the widget
            self.chambers[int(chamber_index) - 1].deleteLater()
            del self.chambers[int(chamber_index) - 1]
        self.n_active -= 1  # Decrement the number of active tasks
