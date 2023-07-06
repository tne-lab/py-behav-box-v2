from __future__ import annotations
from typing import Dict, Any

import msgspec
import typing

from Events.LoggerEvent import LoggerEvent
from Components.Component import Component


T = typing.TypeVar("T")


def subclass_union(cls: typing.Type[T]) -> typing.Type[T]:
    """Returns a Union of all subclasses of `cls` (excluding `cls` itself)"""
    classes = set()

    def _add(cls):
        for c in cls.__subclasses__():
            _add(c)
        classes.add(cls)
    for c in cls.__subclasses__():
        _add(c)
    return typing.Union[tuple(classes)]


class PybEvent(msgspec.Struct, kw_only=True, tag=True, omit_defaults=True, array_like=True):
    metadata: Dict = {}


class ErrorEvent(PybEvent):
    error: BaseException


class CloseSourceEvent(PybEvent):
    pass


class AddTaskEvent(PybEvent):
    chamber: int
    task_name: str
    task_event_loggers: str


class AddLoggerEvent(PybEvent):
    chamber: int
    logger_code: str


class RemoveLoggerEvent(PybEvent):
    chamber: int
    logger_name: str


class ExitEvent(PybEvent):
    pass


class HeartbeatEvent(PybEvent):
    pass


class PygameEvent(PybEvent):
    event_type: int
    event_dict: Dict


class TaskEvent(PybEvent):
    chamber: int


class TimedEvent(TaskEvent, kw_only=True, tag=True, omit_defaults=True, array_like=True):
    timestamp: typing.Optional[float] = None

    def acknowledge(self, timestamp: float):
        self.timestamp = timestamp


class StatefulEvent(TimedEvent):
    pass


class Loggable(TimedEvent):
    def format(self) -> LoggerEvent:
        pass


class OutputFileChangedEvent(TaskEvent):
    output_file: str


class OEEvent(Loggable):
    event_type: str

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.event_type, 0, self.timestamp)


class InfoEvent(Loggable):
    name: str
    value: int

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.name, self.value, self.timestamp)


class StartEvent(TaskEvent):
    pass


class StopEvent(TaskEvent):
    pass


class PauseEvent(Loggable, StatefulEvent):
    def format(self) -> LoggerEvent:
        return LoggerEvent(self, "", 0, self.timestamp)


class ResumeEvent(Loggable, StatefulEvent):
    def format(self) -> LoggerEvent:
        return LoggerEvent(self, "", 0, self.timestamp)


class InitEvent(TaskEvent):
    pass


class ClearEvent(TaskEvent):
    del_loggers: bool


class ComponentUpdateEvent(TimedEvent):
    comp_id: str
    value: Any


class ComponentRegisterEvent(PybEvent):
    chamber: int
    comp: Component


class ComponentCloseEvent(PybEvent):
    comp_id: str


class TaskCompleteEvent(TaskEvent):
    pass


class ComponentChangedEvent(Loggable, StatefulEvent):
    comp: Component
    index: int

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.comp.id, self.index, self.timestamp)


class TimeoutEvent(Loggable, StatefulEvent):
    name: str

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.name, 0, self.timestamp)


class GUIEvent(Loggable, StatefulEvent):
    name: str
    value: int

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.name, self.value, self.timestamp)


class StateEnterEvent(Loggable, StatefulEvent):
    name: str
    value: int

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.name, self.value, self.timestamp)


class StateExitEvent(Loggable, StatefulEvent):
    name: str
    value: int

    def format(self) -> LoggerEvent:
        return LoggerEvent(self, self.name, self.value, self.timestamp)
