from __future__ import annotations
import asyncio
from abc import abstractmethod, ABC
from enum import Enum
from typing import Dict, Any, TYPE_CHECKING

import pygame.event

from Events.LoggerEvent import LoggerEvent

if TYPE_CHECKING:
    from Components.Component import Component
    from Tasks.Task import Task


class PybEvent:
    pass


class HeartbeatEvent(PybEvent):
    pass


class PygameEvent(PybEvent):
    def __init__(self, event: pygame.event.Event):
        self.event = event


class TaskEvent(PybEvent):
    def __init__(self, task: Task, metadata: Dict = None):
        self.task = task
        self.metadata = metadata


class StatefulEvent(TaskEvent):
    pass


class Loggable(ABC, TaskEvent):
    @abstractmethod
    def format(self) -> LoggerEvent:
        pass


class OEEvent(Loggable):
    def __init__(self, task: Task, event_type: str, metadata: Dict = None):
        super().__init__(task, metadata)
        self.event_type = event_type

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.event_type, 0, self.task.time_elapsed())


class InfoEvent(Loggable):
    def __init__(self, task: Task, event: Enum, metadata: Dict = None):
        super().__init__(task, metadata)
        self.event = event

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.event.name, self.event.value, self.task.time_elapsed())


class StartEvent(TaskEvent):
    pass


class StopEvent(TaskEvent):
    pass


class PauseEvent(Loggable, StatefulEvent):
    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.task.state.name, self.task.state.name.value, self.task.time_elapsed())


class ResumeEvent(Loggable, StatefulEvent):
    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.task.state.name, self.task.state.name.value, self.task.time_elapsed())


class InitEvent(TaskEvent):
    pass


class ClearEvent(TaskEvent):
    def __init__(self, task: Task, del_loggers: bool, done: asyncio.Event):
        super().__init__(task)
        self.del_loggers = del_loggers
        self.done = done


class ComponentUpdateEvent(TaskEvent):
    def __init__(self, task: Task, comp_id: str, value: Any, metadata: Dict = None):
        super().__init__(task, metadata)
        self.comp_id = comp_id
        self.value = value


class TaskCompleteEvent(TaskEvent):
    pass


class ComponentChangedEvent(Loggable, StatefulEvent):
    def __init__(self, task: Task, comp: Component, metadata: Dict):
        super().__init__(task, metadata)
        self.comp = comp

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.comp.id, self.task.components[self.comp.id][1], self.task.time_elapsed())


class TimeoutEvent(StatefulEvent):
    def __init__(self, task: Task, name: str, metadata: Dict):
        super().__init__(task, metadata)
        self.name = name


class GUIEvent(Loggable, StatefulEvent):
    def __init__(self, task: Task, event: Enum, metadata: Dict):
        super().__init__(task, metadata)
        self.event = event

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.event.name, self.event.value, self.task.time_elapsed())


class StateEnterEvent(Loggable, StatefulEvent):
    def __init__(self, task: Task, state: Enum, metadata: Dict = None):
        super().__init__(task, metadata)
        self.state = state

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.state.name, self.state.value, self.task.time_elapsed())


class StateExitEvent(Loggable, StatefulEvent):
    def __init__(self, task: Task, state: Enum, metadata: Dict):
        super().__init__(task, metadata)
        self.state = state

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.state.name, self.state.value, self.task.time_elapsed())
