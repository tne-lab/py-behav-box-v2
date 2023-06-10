from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Components.Component import Component
    from Tasks.Task import Task

from abc import ABCMeta, abstractmethod
from Tasks.TaskEvents import ComponentUpdateEvent


class Source:
    __metaclass__ = ABCMeta
    """
    Abstract class defining the base requirements for an input/output source. Sources provide data to and receive data
    from components.
    
    Methods
    -------
    register_component(task, component)
        Registers a Component from a specified Task with the Source.
    close_source()
        Safely closes any connections the Source or its components may have
    read_component(component_id)
        Queries the current input to the component described by component_id
    write_component(component_id, msg)
        Sends data msg to the component described by component_id
    """

    def __init__(self):
        self.components = {}
        self.tasks = {}

    def register_component(self, task: Task, component: Component) -> None:
        self.tasks[component.id] = task
        self.components[component.id] = component

    def update_component(self, cid: str, value: Any) -> None:
        self.tasks[cid].task_thread.queue.put(ComponentUpdateEvent(cid, value, {"value": value}), block=False)

    def close_source(self) -> None:
        pass

    def close_component(self, component_id: str) -> None:
        pass

    def read_component(self, component_id: str) -> Any:
        pass

    def write_component(self, component_id: str, msg: Any) -> None:
        pass

    @abstractmethod
    def is_available(self):
        raise NotImplementedError
