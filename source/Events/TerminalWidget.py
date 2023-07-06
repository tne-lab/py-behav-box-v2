from __future__ import annotations

from Events import PybEvents
from Events.EventWidget import EventWidget

from PyQt5.QtWidgets import QWidget

from Workstation.ScrollLabel import ScrollLabel


class TerminalWidget(EventWidget):

    def __init__(self, name: str):
        super().__init__(name)
        self.event_log = ScrollLabel()
        self.event_log.setMaximumHeight(100)
        self.event_log.setMinimumHeight(100)
        self.event_log.verticalScrollBar().rangeChanged.connect(
            lambda: self.event_log.verticalScrollBar().setValue(self.event_log.verticalScrollBar().maximum()))
        self.cur_text = None

    def handle_event(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StartEvent):
            self.start()
        elif isinstance(event, PybEvents.Loggable):
            event_text = self.format_event(event.format(), type(event).__name__)
            self.cur_text = event_text if self.cur_text is None else "\n".join((self.cur_text, event_text))
            self.event_count += 1
            self.event_log.setText(self.cur_text)

    def get_widget(self) -> QWidget:
        return self.event_log

    def start(self) -> None:
        self.cur_text = None
        self.event_log.setText("")
