from __future__ import annotations

import importlib
import traceback
from multiprocessing import Process
from typing import TYPE_CHECKING, Any, Dict, List

import msgspec.msgpack

from pybehave.Events import PybEvents

if TYPE_CHECKING:
    from pybehave.Components.Component import Component

from abc import ABCMeta
from pybehave.Events.PybEvents import ComponentUpdateEvent, UnavailableSourceEvent
import pybehave.Utilities.Exceptions as pyberror


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
        self.decoder = msgspec.msgpack.Decoder(type=List[PybEvents.subclass_union(PybEvents.PybEvent)], dec_hook=PybEvents.dec_hook, ext_hook=PybEvents.ext_hook)
        self.encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)
        try:
            self.initialize()
            while True:
                events = self.decoder.decode(self.queue.recv_bytes())
                if not self.handle_events(events):
                    return
        except pyberror.ComponentRegisterError as e:
            self.queue.send_bytes(self.encoder.encode(PybEvents.ErrorEvent(type(e).__name__, traceback.format_exc(), metadata={"error_type": "Source Non-Fatal", "chamber": e.chamber, "sid": self.sid})))
        except BaseException as e:
            self.queue.send_bytes(self.encoder.encode(PybEvents.ErrorEvent(type(e).__name__, traceback.format_exc(), metadata={"error_type": "Source Fatal", "sid": self.sid})))
            self.unavailable()
            raise

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
            elif isinstance(event, PybEvents.ConstantsUpdateEvent):
                self.constants_updated(event)
        return True

    def register_component_(self, event: PybEvents.ComponentRegisterEvent):
        component_type = getattr(importlib.import_module("pybehave.Components." + event.comp_type), event.comp_type)
        component = component_type(None, event.cid, event.address)
        component.initialize(event.metadata)
        self.components[component.id] = component
        self.component_chambers[component.id] = event.metadata["chamber"]
        self.register_component(component, event.metadata)

    def register_component(self, component: Component, metadata: Dict) -> None:
        """ Can be overridden to configure connection from the task to the selected component.

        Parameters
        ----------
        component : Component
            the new Component to be registered with the Source
        metadata : dict
            any metadata associated with this Component
        """
        pass

    def update_component(self, cid: str, value: Any, metadata: Dict = None) -> None:
        """ This method should be called to indicate a Component has updated based on new information from the Source.

        Parameters
        ----------
        cid : str
            the ID associated with the updated Component
        value : Any
            the new value received from the Source for the Component
        metadata : dict
            any metadata associated with this update
        """
        metadata = metadata or {}
        self.queue.send_bytes(self.encoder.encode(ComponentUpdateEvent(self.component_chambers[cid], cid, value, metadata=metadata)))

    def close_source_(self):
        self.close_source()
        self.unavailable()

    def close_source(self) -> None:
        """Override to close all connections with the interface represented by the Source."""
        pass

    def close_component(self, component_id: str) -> None:
        """Override to close the connection between a specific component and the interface represented by the Source."""
        pass

    def write_component(self, component_id: str, msg: Any) -> None:
        """ Can be overridden to implement behavior for modifying the value of the indicated component through the interface represented by the Source.

        Parameters
        ----------
        component_id : str
            the ID associated with a Component connected to the Source that should be updated
        msg : Any
            the new value for the Component
        """
        pass

    def output_file_changed(self, event: PybEvents.OutputFileChangedEvent) -> None:
        """Override to implement behavior that should be executed when the output file is changed in the Workstation GUI."""
        pass

    def constants_updated(self, event: PybEvents.ConstantsUpdateEvent) -> None:
        """Override to implement behavior that should be executed when constants are updated through the SubjectConfiguration widget."""
        pass

    def unavailable(self):
        """Call to signal to other processes that the Source has lost connection to the hardware."""
        self.available = False
        self.queue.send_bytes(self.encoder.encode(UnavailableSourceEvent(self.sid)))

    def component_unavailable(self, comp):
        self.queue.send_bytes(self.encoder.encode(
            PybEvents.ErrorEvent(pyberror.ComponentUnavailableError.__name__, traceback.format_exc(),
                                 metadata={"error_type": "Source Non-Fatal", "chamber": comp.metadata['chamber'], "cid": comp.id, "sid": self.sid})))

    @staticmethod
    def metadata_defaults(comp_type: Component.Type = None) -> Dict:
        """Call to get the metadata names and default values required by this source."""
        return {}
