from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from Tasks.Task import Task
    from enum import Enum

from Events.Event import Event


class StateChangeEvent(Event):
    """
        Class defining an Event for a Task state change.

        Attributes
        ----------
        initial_state : Enum
            Enumerated variable representing the initial state of the Task
        new_state : Enum
            Enumerated variable representing the new state of the Task
    """

    def __init__(self, task: Task, initial_state: Enum, new_state: Enum, metadata: Any = None):
        super().__init__(task, metadata)
        self.initial_state = initial_state
        self.new_state = new_state
