from Events.GUIEventLogger import GUIEventLogger
from Events.InputEvent import InputEvent
from enum import Enum
from PyQt5.QtWidgets import *


class ManualEventLogger(GUIEventLogger):

    def __init__(self):
        super().__init__()
        self.widget = QGroupBox('Manual Event')
        manual_layout = QHBoxLayout(self.widget)
        input_layout = QVBoxLayout(self.widget)
        self.widget.setLayout(manual_layout)
        manual_box = QGroupBox('Details')
        self.manual_input = QLineEdit("")
        l1 = QVBoxLayout(self.widget)
        manual_box.setLayout(l1)
        l1.addWidget(self.manual_input)
        code_box = QGroupBox('Code')
        self.code_input = QLineEdit("0")
        l2 = QVBoxLayout(self.widget)
        code_box.setLayout(l2)
        l2.addWidget(self.code_input)
        manual_layout.addWidget(manual_box)
        input_layout.addWidget(code_box)
        self.send = QPushButton()
        self.send.setText("Send")
        self.send.clicked.connect(self.send_event)
        input_layout.addWidget(self.send)
        manual_layout.addLayout(input_layout)

    def send_event(self):
        temp_enum = Enum('TempEnum', {'MANUAL': int(self.code_input.text())})
        self.cw.task.events.append(
            InputEvent(self.cw.task, temp_enum.MANUAL, {"desc": self.manual_input.text()}))

    def log_events(self, events):
        pass

    def get_widget(self):
        return self.widget

    def close(self):
        pass
