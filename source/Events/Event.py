from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Tasks.Task import Task

from typing import Any


class Event:
    """
        Simple class defining the base requirements for a Task Event.

        Attributes
        ----------
        task : Task
            Task the event corresponds to
        metadata : Object
            Any metadata related to the Event
    """

    def __init__(self, task: Task, metadata: Any = None):
        self.task = task
        self.entry_time = task.cur_time - task.start_time
        self.metadata = metadata
