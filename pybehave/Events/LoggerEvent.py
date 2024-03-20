from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pybehave.Events.PybEvents import TaskEvent


class LoggerEvent:

    def __init__(self, event: TaskEvent, name: str, eid: int, entry_time: float):
        self.entry_time = entry_time
        self.event = event
        self.name = name
        self.eid = eid


class StopLoggerEvent(LoggerEvent):
    pass
