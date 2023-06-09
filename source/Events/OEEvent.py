from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Tasks.Task import Task

from Events.LoggerEvent import LoggerEvent
from typing import Any


class OEEvent(LoggerEvent):
    def __init__(self, task: Task, event_type: str, metadata: Any = None):
        super().__init__(task, metadata)
        self.event_type = event_type
