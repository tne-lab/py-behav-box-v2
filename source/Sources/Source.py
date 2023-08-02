from __future__ import annotations

import importlib
from multiprocessing import Process
from typing import TYPE_CHECKING, Any, Dict, List

import msgspec.msgpack

from Events import PybEvents

if TYPE_CHECKING:
    from Components.Component import Component

from abc import ABCMeta, abstractmethod
from Events.PybEvents import ComponentUpdateEvent, UnavailableSourceEvent


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
        self.sid = None
        self.components = {}
        self.component_chambers = {}
        self.queue = None
        self.decoder = None
        self.encoder = None
        self.available = True

    def initialize(self):
        pass

    def run(self):
        self.initialize()
        self.decoder = msgspec.msgpack.Decoder(type=List[PybEvents.subclass_union(PybEvents.PybEvent)])
        self.encoder = msgspec.msgpack.Encoder()
        while True:
            events = self.decoder.decode(self.queue.recv_bytes())
            if not self.handle_events(events):
                return

    def handle_events(self, events: List[PybEvents.PybEvent]):
        for event in events:
            if isinstance(event, PybEvents.ComponentUpdateEvent):
                self.write_component(event.comp_id, event.value)
            elif isinstance(event, PybEvents.ComponentRegisterEvent):
                self.register_component_(event)
            elif isinstance(event, PybEvents.ComponentCloseEvent):
                self.close_component(event.comp_id)
            elif isinstance(event, PybEvents.CloseSourceEvent) or isinstance(event, PybEvents.RemoveSourceEvent):
                self.close_source_()
                return False
            elif isinstance(event, PybEvents.OutputFileChangedEvent):
                self.output_file_changed(event)
        return True

    def register_component_(self, event: PybEvents.ComponentRegisterEvent):
        component_type = getattr(importlib.import_module("Components." + event.comp_type), event.comp_type)
        component = component_type(None, event.cid, event.address)
        component.initialize(event.metadata)
        self.components[component.id] = component
        self.component_chambers[component.id] = event.metadata["chamber"]
        self.register_component(component, event.metadata)

    def register_component(self, component: Component, metadata: Dict) -> None:
        pass

    def update_component(self, cid: str, value: Any, metadata: Dict = None) -> None:
        metadata = metadata or {}
        self.queue.send_bytes(self.encoder.encode(ComponentUpdateEvent(self.component_chambers[cid], cid, value, metadata=metadata)))

    def close_source_(self):
        self.close_source()
        self.unavailable()

    def close_source(self) -> None:
        pass

    def close_component(self, component_id: str) -> None:
        pass

    def write_component(self, component_id: str, msg: Any) -> None:
        pass

    def output_file_changed(self, event: PybEvents.OutputFileChangedEvent) -> None:
        pass

    def unavailable(self):
        self.available = False
        self.queue.send_bytes(self.encoder.encode(UnavailableSourceEvent(self.sid)))
