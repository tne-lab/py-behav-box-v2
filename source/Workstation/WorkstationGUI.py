from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
import csv
import re
import importlib
from Workstation.AddTaskDialog import AddTaskDialog
from Workstation.SettingsDialog import SettingsDialog
from Workstation.ChamberWidget import ChamberWidget


class WorkstationGUI(QWidget):
    def __init__(self, workstation):
        QWidget.__init__(self)
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

        # Callback to pygame (once every millisecond)
        self.timer = QTimer()
        self.timer.timeout.connect(self.workstation.loop)
        self.timer.setInterval(1)
        self.timer.start()

        self.setLayout(self.chamber_container)
        self.move(0, 0)
        self.show()

    def settings_dialog(self):
        # Opens the SettingsDialog for adjusting py-behav settings
        sd = SettingsDialog(self.workstation)
        if sd.exec():
            settings = QSettings()
            settings.setValue("n_chamber", sd.n_chamber.text())
            self.workstation.compute_chambergui()

    def task_dialog(self):
        # Opens the AddTaskDialog for adding a new task to a chamber
        td = AddTaskDialog(self.workstation)
        if td.exec():
            if td.configuration_path is not None:  # If a configuration file was provided
                with open(td.configuration_path, newline='') as csvfile:  # Open the configuration file
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
                            task = td.tasks.index(row[1])
                        elif row[0] == "Address File":
                            afp = row[1]
                        elif row[0] == "Protocol":
                            pfp = row[1]
                        elif row[0] == "Prompt":
                            prompt = row[1]
                        elif row[0] == "EventLoggers":
                            types = list(map(lambda x: x.split("))")[-1], row[1].split("((")))  # Get the type of each logger
                            params = list(map(lambda x: x.split("((")[-1], row[1].split("))")))  # Get the parameters for each logger
                            for i in range(len(types) - 1):
                                logger_type = getattr(importlib.import_module("Events." + types[i]), types[i])  # Import the logger
                                param_vals = re.findall("\|\|(.+?)\|\|", params[i])  # Extract the parameters
                                event_loggers.append(logger_type(*param_vals))  # Instantiate the logger
                                logger_params.append(param_vals)

                    self.add_task(chamber, task, subject, afp, pfp, prompt, (event_loggers, logger_params))
            else:
                self.add_task(td.chamber.currentText(), td.task.currentIndex())

    def add_task(self, chamber_index, task_index, subject="default", afp="", pfp="", prompt="", event_loggers=([], [])):
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
            self.chambers[int(chamber_index) - 1] = ChamberWidget(self, chamber_index, task_index, subject, afp, pfp, prompt, event_loggers)
            self.chamber_container.insertWidget(self.n_active, self.chambers[int(chamber_index) - 1])
            self.n_active += 1  # Increment the number of active chambers
        else:  # The chamber is already in use
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Chamber already occupied, clear before adding a new task')
            msg.setWindowTitle("Error")
            msg.exec_()

    def remove_task(self, chamber_index):
        """
        Removes a task

        Parameters
        ----------
        chamber_index : str
            The index of the task
        """
        self.workstation.remove_task(int(chamber_index) - 1)  # Remove the task from the main Workstation
        self.chamber_container.removeWidget(self.chambers[int(chamber_index) - 1])  # Remove the widget
        self.chambers[int(chamber_index) - 1].deleteLater()
        del self.chambers[int(chamber_index) - 1]
        self.n_active -= 1  # Decrement the number of active tasks
