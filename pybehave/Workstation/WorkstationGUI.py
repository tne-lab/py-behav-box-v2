from __future__ import annotations

import os
import webbrowser
from typing import TYPE_CHECKING, List

from pybehave.Events.Widget import Widget
from pybehave.Utilities.Exceptions import AddTaskError
from pybehave.Workstation.AddressFileCreationDialog import AddressFileCreationDialog
from pybehave.Workstation.ProtocolCreationDialog import ProtocolCreationDialog
from pybehave.Workstation.SelectTaskDialog import SelectTaskDialog

if TYPE_CHECKING:
    from pybehave.Workstation.Workstation import Workstation

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from pybehave.Workstation.AddTaskDialog import AddTaskDialog
from pybehave.Workstation.SettingsDialog import SettingsDialog
from pybehave.Workstation.ChamberWidget import ChamberWidget
from pybehave.Workstation.ErrorMessageBox import ErrorMessageBox


class WorkstationGUI(QWidget):
    error = pyqtSignal(str, name="error_signal")

    def __init__(self, workstation: Workstation):
        QWidget.__init__(self)
        self.sd = None
        self.td = None
        self.afcd = None
        self.std = None
        self.pcd = None
        self.emsg = None
        self.ignore_errors = False
        self.n_active = 0
        self.workstation = workstation
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)

        self.setWindowTitle("Pybehave")
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
        add_task = action_file.addAction("Add Chamber")  # Action for adding a new task to a chamber
        add_task.triggered.connect(self.task_dialog)  # Call task_dialog method when clicked
        settings = action_file.addAction("Settings")  # Action for adjusting py-behav settings
        settings.triggered.connect(self.settings_dialog)  # Call settings_dialog method when clicked
        address_files = action_file.addMenu("AddressFiles")
        new_address_file = address_files.addAction("New")
        new_address_file.triggered.connect(lambda: self.select_task_dialog(True))
        edit_address_file = address_files.addAction("Edit")
        edit_address_file.triggered.connect(lambda: self.select_task_dialog(True, True))
        protocols = action_file.addMenu("Protocols")
        new_protocol = protocols.addAction("New")
        new_protocol.triggered.connect(lambda: self.select_task_dialog(False))
        edit_protocol = protocols.addAction("Edit")
        edit_protocol.triggered.connect(lambda: self.select_task_dialog(False, True))
        action_file.addSeparator()
        quit_gui = action_file.addAction("Quit")  # Quits py-behav
        quit_gui.triggered.connect(self.close)
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

    def select_task_dialog(self, is_addressfile, edit: bool = False):
        # Opens a dialog to select the task to use for creating/editing an AddressFile or Protocol
        self.std = SelectTaskDialog(self, is_addressfile, edit)
        self.std.show()

    def address_file_dialog(self, task: str, file_path: str = None) -> None:
        # Opens the AddressFile creator
        self.afcd = AddressFileCreationDialog(self, task, file_path)
        self.afcd.show()

    def protocol_dialog(self, task: str, file_path: str = None) -> None:
        # Opens the Protocol creator
        self.pcd = ProtocolCreationDialog(self, task, file_path)
        self.pcd.show()

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
            self.emsg = ErrorMessageBox(self, message)
            self.emsg.show()

    def confirm_exit(self):
        emsg = QMessageBox(self)
        emsg.setIcon(QMessageBox.Warning)
        emsg.setText("A task is currently running.")
        emsg.setInformativeText("Do you want to stop the task(s) and exit?")
        emsg.setWindowTitle("Confirm Exit")

        emsg.addButton("Cancel", QMessageBox.RejectRole)
        stop_exit_button = emsg.addButton("Stop Task(s) and Exit", QMessageBox.AcceptRole)

        emsg.exec_()

        return emsg.clickedButton() == stop_exit_button

    def closeEvent(self, event):
        task_running = any(gui.started and not gui.paused for gui in self.workstation.guis.values())
        if task_running:
            if self.confirm_exit():
                self.workstation.exit(stop_tasks=True)
                event.accept()
            else:
                event.ignore()
        else:
            self.workstation.exit()
            event.accept()
