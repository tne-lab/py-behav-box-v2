from Events import PybEvents
from Events.GUIEventLogger import GUIEventLogger
from PyQt5.QtWidgets import *

from Events.LoggerEvent import LoggerEvent


class ManualEventLogger(GUIEventLogger):

    class ManualEvent(PybEvents.Loggable, PybEvents.StatefulEvent):
        def format(self) -> LoggerEvent:
            return LoggerEvent(self, self.task.state.name, self.task.state.name.value, self.task.time_elapsed())

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

    def send_event(self) -> None:
        self.cw.workstation.queue.put_nowait(self.ManualEvent(self.cw.task))

    async def log_event(self, events: LoggerEvent) -> None:
        pass

    def get_widget(self) -> QWidget:
        return self.widget
