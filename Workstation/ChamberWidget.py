from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pkgutil
import os
from datetime import datetime
from Workstation.IconButton import IconButton
from Workstation.ScrollLabel import ScrollLabel
from Events.ConsoleLogger import ConsoleLogger


class ChamberWidget(QGroupBox):
    def __init__(self, workstation, chamber_index, task_index, parent=None):
        super(ChamberWidget, self).__init__(parent)
        self.workstation = workstation
        chamber = QVBoxLayout(self)
        chamber_bar = QVBoxLayout(self)
        row1 = QHBoxLayout(self)
        self.chamber_id = QLabel(chamber_index)
        self.chamber_id.setFont(QFont('Arial', 32))
        row1.addWidget(self.chamber_id)
        subject_box = QGroupBox('Subject')
        subject_box_layout = QHBoxLayout(self)
        subject_box.setLayout(subject_box_layout)
        self.subject = QLineEdit("default")
        self.subject.textChanged.connect(self.subject_changed)
        subject_box_layout.addWidget(self.subject)
        row1.addWidget(subject_box)
        task_box = QGroupBox('Task')
        task_box_layout = QHBoxLayout(self)
        task_box.setLayout(task_box_layout)
        self.task_name = QComboBox()
        tasks = []
        for f in pkgutil.iter_modules(['Tasks']):
            if not f.name == "Task":
                tasks.append(f.name)
        self.task_name.addItems(tasks)
        self.task_name.setCurrentIndex(task_index)
        task_box_layout.addWidget(self.task_name)
        row1.addWidget(task_box)
        chamber_bar.addLayout(row1)
        row2 = QHBoxLayout(self)
        address_file = QGroupBox('Address File')
        address_file_layout = QHBoxLayout(self)
        address_file.setLayout(address_file_layout)
        self.address_file_path = QLineEdit("")
        self.address_file_path.setReadOnly(True)
        address_file_layout.addWidget(self.address_file_path)
        address_file_browse = QPushButton()
        address_file_browse.setIcon(QIcon('Workstation/icons/folder.svg'))
        address_file_browse.setFixedWidth(30)
        address_file_browse.clicked.connect(lambda: self.get_file_path(self.address_file_path, "AddressFiles"))
        address_file_layout.addWidget(address_file_browse)
        row2.addWidget(address_file)
        protocol_file = QGroupBox('Protocol')
        protocol_file_layout = QHBoxLayout(self)
        protocol_file.setLayout(protocol_file_layout)
        self.protocol_path = QLineEdit("")
        self.protocol_path.setReadOnly(True)
        protocol_file_layout.addWidget(self.protocol_path)
        protocol_file_browse = QPushButton()
        protocol_file_browse.setIcon(QIcon('Workstation/icons/folder.svg'))
        protocol_file_browse.setFixedWidth(30)
        protocol_file_browse.clicked.connect(lambda: self.get_file_path(self.protocol_path, "Protocols"))
        protocol_file_layout.addWidget(protocol_file_browse)
        row2.addWidget(protocol_file)
        chamber_bar.addLayout(row2)
        row3 = QHBoxLayout(self)
        output_file = QGroupBox('Output Folder')
        output_file_layout = QHBoxLayout(self)
        output_file.setLayout(output_file_layout)
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.output_file_path = QLineEdit(
            "{}/py-behav/{}/Data/{}/{}/".format(desktop, self.task_name.currentText(), self.subject.text(),
                                                datetime.now().strftime("%m-%d-%Y")))
        output_file_layout.addWidget(self.output_file_path)
        row3.addWidget(output_file)
        session_box = QGroupBox('Session')
        session_layout = QHBoxLayout(self)
        session_box.setLayout(session_layout)
        self.play_button = IconButton('Workstation/icons/play.svg', 'Workstation/icons/play_hover.svg')
        self.play_button.setFixedWidth(30)
        self.play_button.clicked.connect(self.play_pause)
        session_layout.addWidget(self.play_button)
        stop_button = IconButton('Workstation/icons/stop.svg', 'Workstation/icons/stop_hover.svg')
        stop_button.setFixedWidth(30)
        session_layout.addWidget(stop_button)
        row3.addWidget(session_box)
        chamber_bar.addLayout(row3)
        chamber.addLayout(chamber_bar)
        self.event_log = ScrollLabel()
        self.event_log.setText("Event 1\nEvent 2\nEvent 3\nEvent 4\nEvent 5\nEvent 6\nEvent 7\nEvent 8")
        self.event_log.setMaximumHeight(100)
        self.event_log.setMinimumHeight(100)
        chamber.addWidget(self.event_log)
        self.setLayout(chamber)
        self.workstation.add_task(int(chamber_index) - 1, self.task_name.currentText(),
                                  self.workstation.sources, self.address_file_path.text(),
                                  self.protocol_path.text(), ConsoleLogger())
        self.task = self.workstation.tasks[int(chamber_index) - 1]

    def get_file_path(self, le, dir_type):
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        file_name = QFileDialog.getOpenFileName(self, 'Select File',
                                                "{}/py-behav/{}/{}/".format(desktop, self.task_name.currentText(),
                                                                            dir_type),
                                                '*.csv')
        if len(file_name[0]) > 0:
            le.setText(file_name[0])
            self.workstation.remove_task(int(self.chamber_id.text()) - 1)
            self.workstation.add_task(int(self.chamber_id.text()) - 1, self.task_name.currentText(),
                                      self.workstation.sources, self.address_file_path.text(),
                                      self.protocol_path.text(), ConsoleLogger())

    def play_pause(self):
        if not self.task.started:
            self.task.start()
            self.play_button.icon = 'Workstation/icons/pause.svg'
            self.play_button.hover_icon = 'Workstation/icons/pause_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
        elif self.task.paused:
            self.task.resume()
            self.play_button.icon = 'Workstation/icons/pause.svg'
            self.play_button.hover_icon = 'Workstation/icons/pause_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))
        else:
            self.task.pause()
            self.play_button.icon = 'Workstation/icons/play.svg'
            self.play_button.hover_icon = 'Workstation/icons/play_hover.svg'
            self.play_button.setIcon(QIcon(self.play_button.icon))

    def subject_changed(self):
        self.task.metadata["subject"] = self.subject.text()
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.output_file_path.setText(
            "{}/py-behav/{}/Data/{}/{}/".format(desktop, self.task_name.currentText(), self.subject.text(),
                                                datetime.now().strftime("%m-%d-%Y")))
