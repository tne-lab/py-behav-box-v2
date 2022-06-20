from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import pkgutil
import os
import csv
from datetime import datetime
from Workstation.IconButton import IconButton
from Workstation.ConfigurationDialog import ConfigurationDialog
from Events.TextEventLogger import TextEventLogger
from Events.FileEventLogger import FileEventLogger
from Events.GUIEventLogger import GUIEventLogger


class ChamberWidget(QGroupBox):
    def __init__(self, wsg, chamber_index, task_index, sn="default", afp="", pfp="", prompt="", event_loggers=([], []),
                 parent=None):
        super(ChamberWidget, self).__init__(parent)
        self.workstation = wsg.workstation
        self.wsg = wsg
        self.chamber = QVBoxLayout(self)
        row1 = QHBoxLayout(self)

        # Widget corresponding to the chamber number that contains this task
        self.chamber_id = QLabel(chamber_index)
        self.chamber_id.setFont(QFont('Arial', 32))
        row1.addWidget(self.chamber_id)

        # Widget corresponding to the name of subject completing this task
        subject_box = QGroupBox('Subject')
        subject_box_layout = QHBoxLayout(self)
        subject_box.setLayout(subject_box_layout)
        self.subject = QLineEdit(sn)
        self.subject.textChanged.connect(self.subject_changed)
        subject_box_layout.addWidget(self.subject)
        row1.addWidget(subject_box)

        # Widget corresponding to the name of the task being completed
        task_box = QGroupBox('Task')
        task_box_layout = QHBoxLayout(self)
        task_box.setLayout(task_box_layout)
        self.task_name = QComboBox()
        tasks = []
        for f in pkgutil.iter_modules(['Tasks']):  # Get all classes in the Tasks folder
            if not f.name == "Task":  # Ignore the abstract class
                tasks.append(f.name)
        self.task_name.addItems(tasks)
        self.task_name.setCurrentIndex(task_index)
        task_box_layout.addWidget(self.task_name)
        row1.addWidget(task_box)

        self.chamber.addLayout(row1)
        row2 = QHBoxLayout(self)

        # Widget corresponding to the path to the address file. A blank path indicates the default is being used
        address_file = QGroupBox('Address File')
        address_file_layout = QHBoxLayout(self)
        address_file.setLayout(address_file_layout)
        self.address_file_path = QLineEdit(afp)
        self.address_file_path.setReadOnly(True)
        address_file_layout.addWidget(self.address_file_path)
        self.address_file_browse = QPushButton()
        self.address_file_browse.setIcon(QIcon('Workstation/icons/folder.svg'))
        self.address_file_browse.setFixedWidth(30)
        self.address_file_browse.clicked.connect(lambda: self.get_file_path(self.address_file_path, "AddressFiles"))
        address_file_layout.addWidget(self.address_file_browse)
        row2.addWidget(address_file)

        # Widget corresponding to the path to the protocol file. A blank path indicates the default is being used
        protocol_file = QGroupBox('Protocol')
        protocol_file_layout = QHBoxLayout(self)
        protocol_file.setLayout(protocol_file_layout)
        self.protocol_path = QLineEdit(pfp)
        self.protocol_path.setReadOnly(True)
        protocol_file_layout.addWidget(self.protocol_path)
        self.protocol_file_browse = QPushButton()
        self.protocol_file_browse.setIcon(QIcon('Workstation/icons/folder.svg'))
        self.protocol_file_browse.setFixedWidth(30)
        self.protocol_file_browse.clicked.connect(lambda: self.get_file_path(self.protocol_path, "Protocols"))
        protocol_file_layout.addWidget(self.protocol_file_browse)
        row2.addWidget(protocol_file)

        self.chamber.addLayout(row2)
        row3 = QHBoxLayout(self)

        # Widget corresponding to the path for the output folder for any file event loggers
        output_file = QGroupBox('Output Folder')
        output_file_layout = QHBoxLayout(self)
        output_file.setLayout(output_file_layout)
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.output_file_path = QLineEdit(
            "{}/py-behav/{}/Data/{}/{}/".format(desktop, self.task_name.currentText(), self.subject.text(),
                                                datetime.now().strftime("%m-%d-%Y")))
        self.output_file_path.textChanged.connect(self.output_file_changed)
        output_file_layout.addWidget(self.output_file_path)
        row3.addWidget(output_file)

        # Widget corresponding to controls for playing/pausing/stopping the task
        session_box = QGroupBox('Session')
        session_layout = QHBoxLayout(self)
        session_box.setLayout(session_layout)
        self.play_button = IconButton('Workstation/icons/play.svg', 'Workstation/icons/play_hover.svg')
        self.play_button.setFixedWidth(30)
        self.play_button.clicked.connect(self.play_pause)
        session_layout.addWidget(self.play_button)
        self.stop_button = IconButton('Workstation/icons/stop.svg', 'Workstation/icons/stop_hover.svg',
                                      'Workstation/icons/stop_disabled.svg')
        self.stop_button.setFixedWidth(30)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        session_layout.addWidget(self.stop_button)
        row3.addWidget(session_box)

        self.chamber.addLayout(row3)

        # Message to display before starting task
        self.prompt = prompt

        # Widget corresponding to event loggers
        self.event_loggers = [TextEventLogger()] + event_loggers[0]
        for el in self.event_loggers:
            if isinstance(el, GUIEventLogger):
                el.set_chamber(self)
                self.chamber.addWidget(el.get_widget())

        self.setLayout(self.chamber)
        self.logger_params = event_loggers[1]
        self.workstation.add_task(int(chamber_index) - 1, self.task_name.currentText(), self.address_file_path.text(),
                                  self.protocol_path.text(), self.event_loggers)
        self.task = self.workstation.tasks[int(chamber_index) - 1]
        self.output_file_changed()

    def refresh(self):
        """
        Updates the representation of the Task with the Workstation based on any changes made in the GUI.
        """
        self.workstation.remove_task(int(self.chamber_id.text()) - 1)
        self.workstation.add_task(int(self.chamber_id.text()) - 1, self.task_name.currentText(),
                                  self.address_file_path.text(),
                                  self.protocol_path.text(), self.event_loggers)
        self.task = self.workstation.tasks[int(self.chamber_id.text()) - 1]
        self.output_file_changed()

    def get_file_path(self, le, dir_type):
        """
        Creates a file browser dialog to select a Protocol or Address File.

        Parameters
        ----------
        le  :   QLineEdit
            The widget which will be populated with the path to the file
        dir_type    :   string
            The type of file to look for (Protocols or AddressFiles)
        """
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        file_name = QFileDialog.getOpenFileName(self, 'Select File',
                                                "{}/py-behav/{}/{}/".format(desktop, self.task_name.currentText(),
                                                                            dir_type),
                                                '*.csv')
        if len(file_name[0]) > 0:  # If a file was selected
            le.setText(file_name[0])
            self.refresh()  # Update the Task representation with the new file

    def play_pause(self):
        """
        On click function for the play/pause button. Behavior is different if task has yet to be started, is currently running, or is paused.
        """
        if not self.task.started:  # If the task has yet to be started
            if len(self.prompt) > 0:  # If there is a prompt that should be shown before the task starts
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(self.prompt)
                msg.setWindowTitle("Wait")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg.setDefaultButton(QMessageBox.Cancel)
                if msg.exec_() == QMessageBox.Cancel:  # Stop the task from running if the prompt was cancelled
                    return
            # Change the play to a pause button
            self.play_button.icon = 'Workstation/icons/pause.svg'
            self.play_button.hover_icon = 'Workstation/icons/pause_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
            # Disable all task configuration options
            self.stop_button.setEnabled(True)
            self.subject.setEnabled(False)
            self.task_name.setEnabled(False)
            self.address_file_browse.setEnabled(False)
            self.protocol_file_browse.setEnabled(False)
            self.output_file_path.setEnabled(False)
            self.workstation.start_task(int(self.chamber_id.text()) - 1)  # Start the task with the Workstation
        elif self.task.paused:  # If the task is currently paused
            # Change the pause to a play button
            self.play_button.icon = 'Workstation/icons/pause.svg'
            self.play_button.hover_icon = 'Workstation/icons/pause_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
            self.task.resume()  # Resume the task
        else:  # The task is currently playing
            # Change the play to a pause button
            self.play_button.icon = 'Workstation/icons/play.svg'
            self.play_button.hover_icon = 'Workstation/icons/play_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
            self.task.pause()  # Pause the task

    def stop(self):
        """
        On click function for the stop button.
        """
        # Change the pause to a play button
        self.play_button.icon = 'Workstation/icons/play.svg'
        self.play_button.hover_icon = 'Workstation/icons/play_hover.svg'
        self.play_button.setIcon(QIcon(self.play_button.icon))
        self.stop_button.setEnabled(False)  # Disable the stop button
        # Re-enable all task configuration options
        self.subject.setEnabled(True)
        self.task_name.setEnabled(True)
        self.address_file_browse.setEnabled(True)
        self.protocol_file_browse.setEnabled(True)
        self.output_file_path.setEnabled(True)
        self.workstation.stop_task(int(self.chamber_id.text()) - 1)  # Stop the task with the Workstation

    def subject_changed(self):
        """
        Callback for when the name of the subject is changed in the GUI.
        """
        self.task.metadata["subject"] = self.subject.text()
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        # Create a save path corresponding to the subject
        self.output_file_path.setText(
            "{}/py-behav/{}/Data/{}/{}/".format(desktop, self.task_name.currentText(), self.subject.text(),
                                                datetime.now().strftime("%m-%d-%Y")))
        self.output_file_changed()  # Signal to saving systems that the output directory has changed

    def output_file_changed(self):
        """
        File for handling changes to the desired output directory
        """
        for el in self.event_loggers:  # Allow all EventLoggers to handle the change
            if isinstance(el, FileEventLogger):  # Handle the change for FileEventLoggers
                el.output_folder = self.output_file_path.text()

    def contextMenuEvent(self, event):
        """
        Create the right click menu for the ChamberWidget.

        Parameters
        ----------
        event
        """
        if not self.task.started:  # If the task is not currently running
            menu = QMenu(self)
            save_config = menu.addAction("Save Configuration")  # Saves the current configuration of the chamber
            clear_chamber = menu.addAction("Clear Chamber")  # Alerts the Workstation to remove the Task
            edit_config = menu.addAction("Edit Configuration")  # Edits the Task configuration
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == save_config:  # If the user requests to save the configuration
                desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
                # Create the Configuration folder if it does not already exist
                if not os.path.exists("{}/py-behav/Configurations/".format(desktop)):
                    os.makedirs("{}/py-behav/Configurations/".format(desktop))
                # Create a file dialog so the user can choose the save location
                file_name = QFileDialog.getSaveFileName(self, 'Save Configuration',
                                                        "{}/py-behav/Configurations/{}-{}-{}.csv".format(desktop,
                                                                                                         self.chamber_id.text(),
                                                                                                         self.subject.text(),
                                                                                                         self.task_name.currentText()),
                                                        '*.csv')
                if len(file_name[0]) > 1:
                    with open(file_name[0], "w", newline='') as out:  # Save all configuration variables
                        w = csv.writer(out)
                        w.writerow(["Chamber", self.chamber_id.text()])  # Index of the chamber
                        w.writerow(["Subject", self.subject.text()])  # The name of the subject
                        w.writerow(["Task", self.task_name.currentText()])  # The current Task
                        w.writerow(["Address File", self.address_file_path.text()])  # The Address File used
                        w.writerow(["Protocol", self.protocol_path.text()])  # The Protocol used
                        w.writerow(["Prompt", self.prompt])  # The prompt to show before the task starts
                        el_text = ""
                        for i in range(1,
                                       len(self.event_loggers)):  # Save the necessary information for each associated EventLogger
                            el_text += type(self.event_loggers[i]).__name__ + "((" + ''.join(
                                f"||{w}||" for w in self.logger_params[i - 1]) + "))"
                        w.writerow(["EventLoggers", el_text])
            elif action == clear_chamber:  # Alert the Workstation to remove the task
                self.wsg.remove_task(self.chamber_id.text())
            elif action == edit_config:  # Create a dialog to edit the configuration
                ld = ConfigurationDialog(self)
                ld.exec()
                self.prompt = ld.prompt.text()  # Update the prompt from the configuration
                self.refresh()
