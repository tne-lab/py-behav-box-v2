from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Tasks.Task import Task

from Events.LoggerEvent import LoggerEvent
from enum import Enum
from typing import Any


class InputEvent(LoggerEvent):
    """
        Class defining an Event for an input to the Task.

        Attributes
        ----------
        input_event : Enum
            Enumerated variable representing the type of input
    """

    def __init__(self, task: Task, input_event: Enum, metadata: Any = None):
        super().__init__(task, metadata)
        self.input_event = input_event
