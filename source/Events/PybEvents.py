from __future__ import annotations
import asyncio
from enum import Enum
from typing import Dict, Any, TYPE_CHECKING

import pygame.event

if TYPE_CHECKING:
    from Components.Component import Component


class PybEvent:
    pass


class HeartbeatEvent(PybEvent):
    pass


class PygameEvent(PybEvent):
    def __init__(self, event: pygame.event.Event):
        self.event = event


class TaskEvent:
    def __init__(self, chamber: int, metadata: Dict = None):
        self.chamber = chamber
        self.metadata = metadata


class StartEvent(TaskEvent):
    pass


class StopEvent(TaskEvent):
    pass


class PauseEvent(TaskEvent):
    pass


class ResumeEvent(TaskEvent):
    pass


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


class ComponentChangedEvent(TaskEvent):
    def __init__(self, chamber: int, comp: Component, metadata: Dict):
        super().__init__(chamber, metadata)
        self.comp = comp


class TimeoutEvent(TaskEvent):
    def __init__(self, chamber: int, name: str, metadata: Dict):
        super().__init__(chamber, metadata)
        self.name = name


class GUIEvent(TaskEvent):
    def __init__(self, chamber: int, event: Enum, metadata: Dict):
        super().__init__(chamber, metadata)
        self.event = event


class StateEnterEvent(TaskEvent):
    def __init__(self, chamber: int, state: Enum, metadata: Dict = None):
        super().__init__(chamber, metadata)
        self.state = state


class StateExitEvent(TaskEvent):
    def __init__(self, chamber: int, state: Enum, metadata: Dict):
        super().__init__(chamber, metadata)
        self.state = state
