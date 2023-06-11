from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Events.LoggerEvent import LoggerEvent
    from Tasks.Task import Task

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

    def __init__(self):
        super().__init__()
        self.task = None
        self.event_count = 0
        self.queue = asyncio.Queue()
        self.event_loop = asyncio.create_task(self.run())

    async def run(self):
        while True:
            le = await self.queue.get()
            await self.log_event(le)

    def start_(self):
        self.event_count = 0
        self.start()

    def start(self) -> None:
        pass

    def stop_(self):
        self.stop()

    def stop(self) -> None:
        pass

    def close_(self):
        self.stop_()
        self.event_loop.cancel()
        self.close()

    def close(self) -> None:
        pass

    @abstractmethod
    async def log_event(self, events: LoggerEvent) -> None:
        raise NotImplementedError

    def set_task(self, task: Task) -> None:
        self.task = task

    def format_event(self, le: LoggerEvent, event_type: str):
        return "{},{},{},{},{},\"{}\"\n".format(self.event_count, le.entry_time, event_type,
                                            le.eid, le.name,
                                            str(le.event.metadata))
