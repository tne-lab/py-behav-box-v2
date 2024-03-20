from __future__ import annotations

from typing import TYPE_CHECKING, List

from PyQt5.QtCore import QRegExp

from pybehave.Events import PybEvents
from pybehave.Events.Widget import Widget
from pybehave.Utilities.Exceptions import AddTaskError

if TYPE_CHECKING:
    from pybehave.Workstation.WorkstationGUI import WorkstationGUI

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import pkgutil
import os
import csv
from datetime import datetime

from pybehave.Workstation.IconButton import IconButton
from pybehave.Workstation.ConfigurationDialog import ConfigurationDialog


class ChamberWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fd = self.ld = self.pd = self.workstation = self.wsg = self.chamber = self.chamber_id = None
        self.subject = self.task_name = self.address_file_path = self.address_file_browse = None
        self.protocol_path = self.protocol_file_browse = self.output_file_path = self.play_button = None
        self.stop_button = self.prompt = self.event_loggers = self.widgets = self.widget_params = None
        self.started = self.paused = False

    @classmethod
    def create_widget(cls, wsg: WorkstationGUI, chamber_index: str, task_index: int, sn: str = "default", afp: str = "",
                 pfp: str = "", prompt: str = "", event_loggers: str = "", widgets: List[Widget] = None, widget_params: List[List[str]] = None, parent=None):
        self = ChamberWidget(parent)
        self.fd = None
        self.ld = None
        self.pd = None
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
        rx = QRegExp("^[_a-zA-Z]\\w*$")
        validator = QRegExpValidator(rx, self)
        self.subject = QLineEdit(sn)
        self.subject.setValidator(validator)
        self.subject.editingFinished.connect(self.subject_changed)
        subject_box_layout.addWidget(self.subject)
        row1.addWidget(subject_box)

        # Widget corresponding to the name of the task being completed
        task_box = QGroupBox('Task')
        task_box_layout = QHBoxLayout(self)
        task_box.setLayout(task_box_layout)
        self.task_name = QComboBox()
        tasks = []
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        for f in pkgutil.iter_modules([f'{desktop}/py-behav/Local/Tasks']):
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
        self.address_file_browse.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons/folder.svg')))
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
        self.protocol_file_browse.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons/folder.svg')))
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
        self.play_button = IconButton(os.path.join(os.path.dirname(__file__), 'icons/play.svg'), os.path.join(os.path.dirname(__file__), 'icons/play_hover.svg'))
        self.play_button.setFixedWidth(30)
        self.play_button.clicked.connect(self.play_pause)
        session_layout.addWidget(self.play_button)
        self.stop_button = IconButton(os.path.join(os.path.dirname(__file__), 'icons/stop.svg'), os.path.join(os.path.dirname(__file__), 'icons/stop_hover.svg'),
                                      os.path.join(os.path.dirname(__file__), 'icons/stop_disabled.svg'))
        self.stop_button.setFixedWidth(30)
        self.stop_button.clicked.connect(lambda: self.stop(True))
        session_layout.addWidget(self.stop_button)
        self.stop_button.setDisabled(True)
        self.stop_button.setEnabled(False)
        row3.addWidget(session_box)

        self.chamber.addLayout(row3)

        # Message to display before starting task
        self.prompt = prompt

        self.setLayout(self.chamber)
        self.event_loggers = event_loggers
        self.workstation.add_task(int(chamber_index) - 1, self.task_name.currentText(), self.subject.text(),
                                  self.address_file_path.text(),
                                  self.protocol_path.text(), self.event_loggers)
        self.output_file_changed()

        # Connect to widgets
        self.widgets = widgets
        self.widget_params = widget_params
        for widget in widgets:
            widget.set_chamber(self)
            self.chamber.addWidget(widget)

        return self

    def refresh(self) -> None:
        """
        Updates the representation of the Task with the Workstation based on any changes made in the GUI.
        """
        self.workstation.remove_task(int(self.chamber_id.text()) - 1, False)
        try:
            self.workstation.add_task(int(self.chamber_id.text()) - 1, self.task_name.currentText(),
                                      self.subject.text(), self.address_file_path.text(),
                                      self.protocol_path.text(), self.event_loggers)
            self.output_file_changed()
        except AddTaskError:
            self.wsg.remove_task(int(self.chamber_id.text()))

    def get_file_path(self, le: QLineEdit, dir_type: str):
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
        self.fd = QFileDialog(self)
        self.fd.setFileMode(QFileDialog.ExistingFile)
        self.fd.setViewMode(QFileDialog.List)
        self.fd.setNameFilter("Python files (*.py)")
        self.fd.setDirectory("{}/py-behav/{}/{}/".format(desktop, self.task_name.currentText(), dir_type))
        self.fd.setWindowTitle('Select File')
        self.fd.accept = lambda: self.open_file(le)
        self.fd.show()

    def open_file(self, le: QLineEdit) -> None:
        if len(self.fd.selectedFiles()[0]) > 0:  # If a file was selected
            le.setText(self.fd.selectedFiles()[0])
            self.refresh()  # Update the Task representation with the new file
        super(QFileDialog, self.fd).accept()

    def play_pause(self) -> None:
        """
        On click function for the play/pause button. Behavior is different if task has yet to be started, is currently running, or is paused.
        """
        if not self.started:  # If the task has yet to be started
            if len(self.subject.text()) == 0:
                self.pd = QMessageBox()
                self.pd.setIcon(QMessageBox.Critical)
                self.pd.setText("Subject cannot be blank")
                self.pd.setWindowTitle("Wait")
                self.pd.setStandardButtons(QMessageBox.Abort)
                self.pd.show()
            elif len(self.prompt) > 0:  # If there is a prompt that should be shown before the task starts
                self.pd = QMessageBox()
                self.pd.setIcon(QMessageBox.Warning)
                self.pd.setText(self.prompt)
                self.pd.setWindowTitle("Wait")
                self.pd.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                self.pd.setDefaultButton(QMessageBox.Cancel)
                self.pd.buttons()[0].clicked.connect(self.play_helper)
                self.pd.show()
            else:
                self.play_helper()
        elif self.paused:  # If the task is currently paused
            self.paused = False
            # Change the pause to a play button
            self.play_button.icon = os.path.join(os.path.dirname(__file__), 'icons/pause.svg')
            self.play_button.hover_icon = os.path.join(os.path.dirname(__file__), 'icons/pause_hover.svg')
            self.play_button.setIcon(QIcon(self.play_button.icon))
            self.workstation.mainq.send_bytes(self.workstation.encoder.encode(PybEvents.ResumeEvent(int(self.chamber_id.text()) - 1)))  # Resume the task
        else:  # The task is currently playing
            self.paused = True
            # Change the play to a pause button
            self.play_button.icon = os.path.join(os.path.dirname(__file__), 'icons/play.svg')
            self.play_button.hover_icon = os.path.join(os.path.dirname(__file__), 'icons/play_hover.svg')
            self.play_button.setIcon(QIcon(self.play_button.icon))
            self.workstation.mainq.send_bytes(self.workstation.encoder.encode(PybEvents.PauseEvent(int(self.chamber_id.text()) - 1)))  # Pause the task

    def play_helper(self) -> None:
        self.started = True
        # Change the play to a pause button
        self.play_button.icon = os.path.join(os.path.dirname(__file__), 'icons/pause.svg')
        self.play_button.hover_icon = os.path.join(os.path.dirname(__file__), 'icons/pause_hover.svg')
        self.play_button.setIcon(QIcon(self.play_button.icon))
        # Disable all task configuration options
        self.stop_button.setDisabled(False)
        self.stop_button.setEnabled(True)
        self.subject.setEnabled(False)
        self.task_name.setEnabled(False)
        self.address_file_browse.setEnabled(False)
        self.protocol_file_browse.setEnabled(False)
        self.output_file_path.setEnabled(False)
        self.workstation.mainq.send_bytes(self.workstation.encoder.encode(PybEvents.StartEvent(int(self.chamber_id.text()) - 1)))
        if self.pd is not None:
            super(QMessageBox, self.pd).accept()
            self.pd = None

    def stop(self, from_click=True) -> None:
        """
        On click function for the stop button.
        """
        self.started = False
        self.paused = False
        if from_click:
            self.workstation.mainq.send_bytes(self.workstation.encoder.encode(PybEvents.StopEvent(int(self.chamber_id.text()) - 1)))
        # Change the pause to a play button
        self.play_button.icon = os.path.join(os.path.dirname(__file__), 'icons/play.svg')
        self.play_button.hover_icon = os.path.join(os.path.dirname(__file__), 'icons/play_hover.svg')
        self.play_button.setIcon(QIcon(self.play_button.icon))
        self.stop_button.setDisabled(True)  # Disable the stop button
        self.stop_button.setEnabled(False)
        # Re-enable all task configuration options
        self.subject.setEnabled(True)
        self.task_name.setEnabled(True)
        self.address_file_browse.setEnabled(True)
        self.protocol_file_browse.setEnabled(True)
        self.output_file_path.setEnabled(True)

    def subject_changed(self) -> None:
        """
        Callback for when the name of the subject is changed in the GUI.
        """
        # self.task.metadata["subject"] = self.subject.text()
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        # Create a save path corresponding to the subject
        self.output_file_path.blockSignals(True)
        self.output_file_path.setText(
            "{}/py-behav/{}/Data/{}/{}/".format(desktop, self.task_name.currentText(), self.subject.text(),
                                                datetime.now().strftime("%m-%d-%Y")))
        self.output_file_path.blockSignals(False)
        self.output_file_changed()  # Signal to saving systems that the output directory has changed

    def output_file_changed(self) -> None:
        """
        File for handling changes to the desired output directory
        """
        self.workstation.mainq.send_bytes(self.workstation.encoder.encode(PybEvents.OutputFileChangedEvent(int(self.chamber_id.text()) - 1, self.output_file_path.text(), self.subject.text())))

    def contextMenuEvent(self, _):
        """
        Create the right click menu for the ChamberWidget.

        Parameters
        ----------
        event
        """
        if not self.started:  # If the task is not currently running
            menu = QMenu(self)
            save_config = menu.addAction("Save Configuration")  # Saves the current configuration of the chamber
            save_config.triggered.connect(self.save_configuration)
            clear_chamber = menu.addAction("Clear Chamber")  # Alerts the Workstation to remove the Task
            clear_chamber.triggered.connect(lambda: self.wsg.workstation.remove_task(int(self.chamber_id.text()) - 1))
            edit_config = menu.addAction("Edit Configuration")  # Edits the Task configuration
            edit_config.triggered.connect(self.edit_configuration)
            menu.popup(QCursor.pos())

    def save_configuration(self) -> None:
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        # Create the Configuration folder if it does not already exist
        if not os.path.exists("{}/py-behav/Configurations/".format(desktop)):
            os.makedirs("{}/py-behav/Configurations/".format(desktop))
        # Create a file dialog so the user can choose the save location
        self.fd = QFileDialog(self)
        self.fd.setFileMode(QFileDialog.AnyFile)
        self.fd.setViewMode(QFileDialog.List)
        self.fd.setAcceptMode(QFileDialog.AcceptSave)
        self.fd.setDirectory("{}/py-behav/Configurations/".format(desktop))
        self.fd.selectFile(
            '{}-{}-{}.csv'.format(self.chamber_id.text(), self.subject.text(), self.task_name.currentText()))
        self.fd.setWindowTitle('Save Configuration')
        self.fd.accept = self.save_configuration_
        self.fd.show()

    def save_configuration_(self) -> None:
        if len(self.fd.selectedFiles()[0]) > 0:  # If a file was selected
            with open(self.fd.selectedFiles()[0], "w", newline='') as out:  # Save all configuration variables
                w = csv.writer(out)
                w.writerow(["Chamber", self.chamber_id.text()])  # Index of the chamber
                w.writerow(["Subject", self.subject.text()])  # The name of the subject
                w.writerow(["Task", self.task_name.currentText()])  # The current Task
                w.writerow(["Address File", self.address_file_path.text()])  # The Address File used
                w.writerow(["Protocol", self.protocol_path.text()])  # The Protocol used
                w.writerow(["Prompt", self.prompt])  # The prompt to show before the task starts
                w.writerow(["EventLoggers", self.event_loggers])
                widget_text = ""
                for i in range(len(self.widgets)):  # Save the necessary information for each associated EventLogger
                    widget_text += type(self.widgets[i]).__name__ + "((" + ''.join(
                        f"||{w}||" for w in self.widget_params[i]) + "))"
                w.writerow(["Widgets", widget_text])
        super(QFileDialog, self.fd).accept()

    def edit_configuration(self) -> None:
        self.ld = ConfigurationDialog(self)
        self.ld.show()
