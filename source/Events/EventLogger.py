from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Events.LoggerEvent import LoggerEvent
    from Tasks.Task import Task

from abc import ABCMeta


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

    def __init__(self):
        self.task = None
        self.event_count = 0
        self.started = False

    def start_(self):
        self.event_count = 0
        self.start()
        self.started = True

    def start(self) -> None:
        pass

    def stop_(self) -> None:
        self.started = False
        self.stop()

    def stop(self) -> None:
        pass

    def close_(self):
        if self.started:
            self.stop_()
        self.close()

    def close(self) -> None:
        pass

    def log_event(self, events: LoggerEvent) -> None:
        pass

    def set_task(self, task: Task) -> None:
        self.task = task

    def format_event(self, le: LoggerEvent, event_type: str):
        return "{},{},{},{},{},{}\n".format(self.event_count, le.entry_time, event_type,
                                            le.eid, le.name,
                                            str(le.event.metadata))
