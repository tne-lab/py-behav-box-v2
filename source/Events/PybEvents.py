from __future__ import annotations
import asyncio
from abc import abstractmethod, ABC
from enum import Enum
from typing import Dict, Any, TYPE_CHECKING

import pygame.event

from Events.LoggerEvent import LoggerEvent, StopLoggerEvent

if TYPE_CHECKING:
    from Components.Component import Component
    from Tasks.Task import Task


class PybEvent:
    pass


class ErrorEvent:
    def __init__(self, error: BaseException, metadata: Dict=None):
        self.error = error
        self.metadata = metadata


class AddTaskEvent(PybEvent):
    def __init__(self, chamber: int, task_name: str, subject_name: str, address_file: str, protocol: str, task_event_loggers: str):
        self.chamber = chamber
        self.task_name = task_name
        self.subject_name = subject_name
        self.address_file = address_file
        self.protocol = protocol
        self.task_event_loggers = task_event_loggers


class ExitEvent(PybEvent):
    pass


class HeartbeatEvent(PybEvent):
    pass


class PygameEvent(PybEvent):
    def __init__(self, event: pygame.event.Event):
        self.event = event


class TaskEvent(PybEvent):
    def __init__(self, chamber: int, metadata: Dict = None):
        self.chamber = chamber
        self.metadata = metadata


class StatefulEvent(TaskEvent):
    pass


class Loggable(ABC, TaskEvent):
    @abstractmethod
    def format(self, task: Task) -> LoggerEvent:
        pass


class OEEvent(Loggable):
    def __init__(self, chamber: int, event_type: str, metadata: Dict = None):
        super().__init__(chamber, metadata)
        self.event_type = event_type

    def format(self, task) -> LoggerEvent:
        return LoggerEvent(self, self.event_type, 0, task.time_elapsed())


class InfoEvent(Loggable):
    def __init__(self, chamber: int, event: Enum, metadata: Dict = None):
        super().__init__(chamber, metadata)
        self.event = event

    def format(self, task: Task) -> LoggerEvent:
        return LoggerEvent(self, self.event.name, self.event.value, task.time_elapsed())


class StartEvent(TaskEvent):
    pass


class StopEvent(Loggable):
    def format(self, task: Task) -> StopLoggerEvent:
        return StopLoggerEvent(self, "", 0, task.time_elapsed())


class PauseEvent(Loggable, StatefulEvent):
    def format(self, task: Task) -> LoggerEvent:
        return LoggerEvent(self, task.state.name, task.state.value, task.time_elapsed())


class ResumeEvent(Loggable, StatefulEvent):
    def format(self, task: Task) -> LoggerEvent:
        return LoggerEvent(self, task.state.name, task.state.value, task.time_elapsed())


class InitEvent(TaskEvent):
    pass


class ClearEvent(TaskEvent):
    def __init__(self, chamber: int, del_loggers: bool, done: asyncio.Event):
        super().__init__(chamber)
        self.del_loggers = del_loggers
        self.done = done


class ComponentUpdateEvent(TaskEvent):
    def __init__(self, chamber: int, comp_id: str, value: Any, metadata: Dict = None):
        super().__init__(chamber, metadata)
        self.comp_id = comp_id
        self.value = value


class TaskCompleteEvent(TaskEvent):
    pass


class ComponentChangedEvent(Loggable, StatefulEvent):
    def __init__(self, chamber: int, comp: Component, metadata: Dict):
        super().__init__(chamber, metadata)
        self.comp = comp

    def format(self, task: Task) -> LoggerEvent:
        return LoggerEvent(self, self.comp.id, task.components[self.comp.id][1], task.time_elapsed())


class TimeoutEvent(StatefulEvent):
    def __init__(self, chamber: int, name: str, metadata: Dict):
        super().__init__(chamber, metadata)
        self.name = name


class GUIEvent(Loggable, StatefulEvent):
    def __init__(self, chamber: int, event: Enum, metadata: Dict):
        super().__init__(chamber, metadata)
        self.event = event

    def format(self, task: Task) -> LoggerEvent:
        return LoggerEvent(self, self.event.name, self.event.value, task.time_elapsed())


class StateEnterEvent(Loggable, StatefulEvent):
    def __init__(self, chamber: int, state: Enum, metadata: Dict = None):
        super().__init__(chamber, metadata)
        self.state = state

    def format(self, task: Task) -> LoggerEvent:
        return LoggerEvent(self, self.state.name, self.state.value, task.time_elapsed())


class StateExitEvent(Loggable, StatefulEvent):
    def __init__(self, chamber: int, state: Enum, metadata: Dict):
        super().__init__(chamber, metadata)
        self.state = state

    def format(self, task: Task) -> LoggerEvent:
        return LoggerEvent(self, self.state.name, self.state.value, task.time_elapsed())
