from __future__ import annotations

import os
import webbrowser
from typing import TYPE_CHECKING, List

from Events.Widget import Widget
from Utilities.Exceptions import AddTaskError

if TYPE_CHECKING:
    from Workstation.Workstation import Workstation

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from Workstation.AddTaskDialog import AddTaskDialog
from Workstation.SettingsDialog import SettingsDialog
from Workstation.ChamberWidget import ChamberWidget


class WorkstationGUI(QWidget):
    error = pyqtSignal(str, name="error_signal")
    def __init__(self, workstation: Workstation):
        QWidget.__init__(self)
        self.sd = None
        self.td = None
        self.emsg = None
        self.ignore_errors = False
        self.n_active = 0
        self.workstation = workstation
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)

        self.setWindowTitle("Pybehav")
        self.setGeometry(0, 0, int(settings.value("pyqt/w")), int(settings.value("pyqt/h")))  # Position GUI
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove GUI margins so it is flush with screen
        # Make the GUI background white
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        # Connect signal to error handler
        self.error.connect(self.on_error)

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
        action_help = menubar.addMenu("Help")
        documentation = action_help.addAction("Documentation")  # Action for opening documentation
        documentation.triggered.connect(lambda: webbrowser.open('https://py-behav-box-v2.readthedocs.io/en/dev/'))
        report = action_help.addAction("Report issue...")  # Action for opening documentation
        report.triggered.connect(lambda: webbrowser.open('https://github.com/tne-lab/py-behav-box-v2/issues'))

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

    def add_task(self, chamber_index: str, task_index: int, subject: str = "default", afp: str = "", pfp: str = "", prompt: str = "", event_loggers: str = "", widgets: List[Widget] = None, widget_params: List[List[str]] = None) -> None:
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
            try:
                self.chambers[int(chamber_index) - 1] = ChamberWidget.create_widget(self, chamber_index, task_index, subject, afp, pfp, prompt, event_loggers, widgets, widget_params)
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
        if chamber_index - 1 in self.chambers:
            self.chamber_container.removeWidget(self.chambers[chamber_index - 1])  # Remove the widget
            self.chambers[chamber_index - 1].deleteLater()
            del self.chambers[chamber_index - 1]
        self.n_active -= 1  # Decrement the number of active tasks

    def on_error(self, message):
        if self.emsg is None and not self.ignore_errors:
            self.emsg = QMessageBox(self)
            self.emsg.setIcon(QMessageBox.Critical)
            self.emsg.setText(message)
            self.emsg.setTextInteractionFlags(Qt.TextBrowserInteraction)
            self.emsg.setWindowTitle("Error")
            ignore_cb = QCheckBox("Ignore future errors")
            ignore_cb.stateChanged.connect(self.ignore_errors_changed)
            self.emsg.finished.connect(self.on_error_close)
            self.emsg.setCheckBox(ignore_cb)
            self.emsg.exec_()

    def on_error_close(self):
        self.emsg = None

    def ignore_errors_changed(self, state):
        self.ignore_errors = (state == Qt.Checked)
