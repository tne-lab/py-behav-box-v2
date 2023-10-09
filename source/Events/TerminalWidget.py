from __future__ import annotations

from PyQt5.QtCore import pyqtSlot

from Events import PybEvents
from Events.EventWidget import EventWidget

from PyQt5.QtWidgets import QWidget, QVBoxLayout

from Workstation.ScrollLabel import ScrollLabel


class TerminalWidget(EventWidget):

    def __init__(self, name: str):
        super().__init__(name)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.event_log = ScrollLabel()
        self.layout.addWidget(self.event_log)
        self.event_log.setMaximumHeight(100)
        self.event_log.setMinimumHeight(100)
        self.event_log.verticalScrollBar().rangeChanged.connect(
            lambda: self.event_log.verticalScrollBar().setValue(self.event_log.verticalScrollBar().maximum()))
        self.cur_text = None

    @pyqtSlot()
    def handle_event(self, event: PybEvents.PybEvent):
        super(TerminalWidget, self).handle_event(event)
        if isinstance(event, PybEvents.Loggable):
            event_text = self.format_event(event.format(), type(event).__name__)
            self.cur_text = event_text if self.cur_text is None else "\n".join((self.cur_text, event_text))
            self.event_count += 1
            self.event_log.setText(self.cur_text)

    def start(self) -> None:
        self.cur_text = None
        self.event_log.setText("")
