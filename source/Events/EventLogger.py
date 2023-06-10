from __future__ import annotations

import threading
from queue import Queue, Empty
from threading import Thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Events.LoggerEvent import LoggerEvent
    from Tasks.Task import Task

from abc import ABCMeta


class EventLogger(Thread):
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
        super().__init__()
        self.task = None
        self.event_count = 0
        self.started = False
        self.queue = Queue()
        self.stop_event = threading.Event()

    def start(self):
        self.stop_event.clear()
        self.event_count = 0
        self.begin()
        self.started = True
        super().start()

    def run(self):
        while not self.stop_event.is_set():
            try:
                le = self.queue.get(timeout=0.5)
                self.log_event(le)
            except Empty:
                pass

    def begin(self) -> None:
        pass

    def stop_(self) -> None:
        self.started = False
        self.stop()
        self.stop_event.set()

    def stop(self) -> None:
        pass

    def close_(self):
        if self.started:
            self.stop_()
        self.join()
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
