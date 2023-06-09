from __future__ import annotations

from typing import Any, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from Components.Component import Component
    from enum import Enum


class TaskEvent:
    def __init__(self, metadata: Dict = None):
        self.metadata = metadata


class StartEvent(TaskEvent):
    pass


class StopEvent(TaskEvent):
    pass


class PauseEvent(TaskEvent):
    pass


class ResumeEvent(TaskEvent):
    pass


class ClearEvent(TaskEvent):
    def __init__(self, del_loggers):
        super().__init__()
        self.del_loggers = del_loggers


class ComponentUpdateEvent(TaskEvent):
    def __init__(self, comp_id: str, value: Any, metadata: Dict = None):
        super().__init__(metadata)
        self.comp_id = comp_id
        self.value = value


class HeartbeatEvent(TaskEvent):
    pass


class TaskCompleteEvent(TaskEvent):
    pass


class ComponentChangedEvent(TaskEvent):
    def __init__(self, comp: Component, metadata: Dict):
        super().__init__(metadata)
        self.comp = comp


class TimeoutEvent(TaskEvent):
    def __init__(self, name: str, metadata: Dict):
        super().__init__(metadata)
        self.name = name


class GUIEvent(TaskEvent):
    def __init__(self, event: Enum, metadata: Dict):
        super().__init__(metadata)
        self.event = event


class StateEnterEvent(TaskEvent):
    def __init__(self, state: Enum, metadata: Dict = None):
        super().__init__(metadata)
        self.state = state


class StateExitEvent(TaskEvent):
    def __init__(self, state: Enum, metadata: Dict):
        super().__init__(metadata)
        self.state = state
