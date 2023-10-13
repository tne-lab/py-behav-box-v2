from __future__ import annotations

import multiprocessing
from multiprocessing.connection import PipeConnection
from typing import Dict, Any

import msgspec
import typing

import numpy as np

from Events.LoggerEvent import LoggerEvent
from Components.Component import Component
import uuid

T = typing.TypeVar("T")


class NumpySerializedRepresentation(msgspec.Struct, gc=False, array_like=True):
    dtype: str
    shape: tuple
    data: bytes


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


NUMPY_TYPE_CODE = 1
numpy_array_encoder = msgspec.msgpack.Encoder()
numpy_array_decoder = msgspec.msgpack.Decoder(type=NumpySerializedRepresentation)


def enc_hook(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return msgspec.msgpack.Ext(1, numpy_array_encoder.encode(
            NumpySerializedRepresentation(dtype=obj.dtype.str, shape=obj.shape, data=obj.data)))
    elif isinstance(obj, PipeConnection):
        # Pickle the connection
        return multiprocessing.context.reduction.ForkingPickler.dumps(obj)
    else:
        # Raise a NotImplementedError for other types
        raise NotImplementedError(f"Objects of type {type(obj)} are not supported")


def dec_hook(typ: typing.Type, obj: Any) -> Any:
    # `type` here is the value of the custom type annotation being decoded.
    if typ is PipeConnection:
        # Convert ``obj`` (which should be a ``tuple``) to a complex
        return multiprocessing.context.reduction.ForkingPickler.loads(obj)
    else:
        # Raise a NotImplementedError for other types
        raise NotImplementedError(f"Objects of type {typ} are not supported")


def ext_hook(code: int, data: memoryview) -> Any:
    if code == NUMPY_TYPE_CODE:
        serialized_array_rep = numpy_array_decoder.decode(data)
        return np.frombuffer(serialized_array_rep.data, dtype=serialized_array_rep.dtype).reshape(
            serialized_array_rep.shape)
    else:
        # Raise a NotImplementedError for other extension type codes
        raise NotImplementedError(f"Extension type code {code} is not supported")


class PybEvent(msgspec.Struct, kw_only=True, tag=True, omit_defaults=True, array_like=True):
    metadata: Dict = {}
    trace_id: uuid.UUID = msgspec.field(default_factory=uuid.uuid4)


class ErrorEvent(PybEvent):
    error: str
    traceback: str


class CloseSourceEvent(PybEvent):
    pass


class UnavailableSourceEvent(PybEvent):
    sid: str


class AddSourceEvent(PybEvent):
    sid: str
    conn: PipeConnection


class RemoveSourceEvent(PybEvent):
    sid: str


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
        raise NotImplementedError


class AddTaskEvent(TaskEvent):
    task_name: str
    task_event_loggers: str


class AddLoggerEvent(TaskEvent):
    logger_code: str


class RemoveLoggerEvent(TaskEvent):
    logger_name: str


class OutputFileChangedEvent(TaskEvent):
    output_file: str
    subject: str


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


class ConstantsUpdateEvent(TaskEvent):
    constants: Dict


class ConstantRemoveEvent(TaskEvent):
    constant: str


class ComponentRegisterEvent(PybEvent):
    comp_type: str
    cid: str
    address: typing.Union[str, typing.List[str]]


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
