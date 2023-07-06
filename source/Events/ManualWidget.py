from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QWidget

from Events import PybEvents

from Events.LoggerEvent import LoggerEvent
from Events.Widget import Widget


class ManualWidget(Widget):

    class ManualEvent(PybEvents.Loggable, PybEvents.StatefulEvent):
        name: str
        value: int

        def format(self, timestamp: float) -> LoggerEvent:
            return LoggerEvent(self, self.name, self.value, timestamp)

    def __init__(self, name: str):
        super().__init__(name)
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
        self.cw.workstation.mainq.send_bytes(self.cw.workstation.encoder.encode(self.ManualEvent(int(self.cw.chamber_id.text()) - 1), self.manual_input.text(), int(self.code_input.text())))

    def get_widget(self) -> QWidget:
        return self.widget
