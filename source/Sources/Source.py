from __future__ import annotations

import threading
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, Any, Dict

from Events import PybEvents

if TYPE_CHECKING:
    from Components.Component import Component

from abc import ABCMeta, abstractmethod
from Events.PybEvents import ComponentUpdateEvent


class Source(Process):
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
        super(Source, self).__init__()
        self.components = {}
        self.inq = Queue()
        self.outq = None
        self.read_thread = None

    def initialize(self):
        pass

    def run(self):
        self.read_thread = threading.Thread(target=self.read)
        self.read_thread.start()
        while True:
            event = self.inq.get()
            if isinstance(event, PybEvents.ComponentUpdateEvent):
                self.write_component(event.comp_id, event.value)
            elif isinstance(event, PybEvents.ComponentRegisterEvent):
                self.register_component(event.chamber, event.comp)
            elif isinstance(event, PybEvents.ComponentCloseEvent):
                self.close_component(event.comp_id)
            elif isinstance(event, PybEvents.CloseSourceEvent):
                self.close_source()

    def read(self):
        pass

    def register_component(self, chamber: int, component: Component) -> None:
        self.components[component.id] = (component, chamber)

    def update_component(self, cid: str, value: Any, metadata: Dict = None) -> None:
        self.outq.put(ComponentUpdateEvent(self.components[cid][1], cid, value, metadata))

    def close_source(self) -> None:
        pass

    def close_component(self, component_id: str) -> None:
        pass

    def write_component(self, component_id: str, msg: Any) -> None:
        pass

    @abstractmethod
    def is_available(self):
        raise NotImplementedError
