from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Tasks.Task import Task

from Events.LoggerEvent import LoggerEvent
from enum import Enum
from typing import Any


class FinalStateEvent(LoggerEvent):
    """
        Class defining an Event for a Task's final state.

        Attributes
        ----------
        final_state : Enum
            Enumerated variable representing the final state
    """
    def __init__(self, task: Task, final_state: Enum, metadata: Any = None):
        super().__init__(task, metadata)
        self.final_state = final_state
