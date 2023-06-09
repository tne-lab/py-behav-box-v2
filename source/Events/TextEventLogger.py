from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Events.LoggerEvent import LoggerEvent

from PyQt5.QtWidgets import QWidget

from Events.GUIEventLogger import GUIEventLogger
from Workstation.ScrollLabel import ScrollLabel


class TextEventLogger(GUIEventLogger):

    def __init__(self):
        super().__init__()
        self.event_log = ScrollLabel()
        self.event_log.setMaximumHeight(100)
        self.event_log.setMinimumHeight(100)
        self.event_log.verticalScrollBar().rangeChanged.connect(
            lambda: self.event_log.verticalScrollBar().setValue(self.event_log.verticalScrollBar().maximum()))

    def log_event(self, le: LoggerEvent):
        cur_text = self.event_log.text()
        self.event_count += 1
        cur_text += self.format_event(le, type(le.event).__name__)
        self.event_log.setText(cur_text)

    def get_widget(self) -> QWidget:
        return self.event_log

    def start(self) -> None:
        super(TextEventLogger, self).start()
        self.event_log.setText("")
