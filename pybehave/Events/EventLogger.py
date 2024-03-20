from __future__ import annotations

import collections
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pybehave.Events.LoggerEvent import LoggerEvent
    from pybehave.Tasks.Task import Task

from abc import ABCMeta, abstractmethod


class EventLogger:
    __metaclass__ = ABCMeta
    """
    Abstract class defining the base requirements for an event logging system. Event loggers parse Event objects.

    Methods
    -------
    start()
        Starts the event logger
    close()
        Closes the event logger
    log_events(events)
        Handle each event in the input Event list
    """

    def __init__(self, name: str):
        self.name = name
        self.task = None
        self.event_count = 0

    def start_(self):
        self.event_count = 0
        self.start()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def close_(self):
        self.stop()
        self.close()

    def close(self) -> None:
        pass

    @abstractmethod
    def log_events(self, events: collections.deque[LoggerEvent]) -> None:
        raise NotImplementedError

    def set_task(self, task: Task) -> None:
        self.task = task

    def format_event(self, le: LoggerEvent, event_type: str):
        return "{},{},{},{},{},\"{}\"\n".format(self.event_count, le.entry_time, event_type,
                                                str(le.eid), le.name,
                                                str(le.event.metadata))
