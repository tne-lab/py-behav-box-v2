from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Tasks.Task import Task

from Events.Event import Event
from enum import Enum
from typing import Any


class InitialStateEvent(Event):
    """
        Class defining an Event for a Task's initial state.

        Attributes
        ----------
        initial_state : Enum
            Enumerated variable representing the initial state
    """
    def __init__(self, task: Task, initial_state: Enum, metadata: Any = None):
        super().__init__(task, metadata)
        self.initial_state = initial_state
