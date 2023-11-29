from __future__ import annotations

import importlib
import runpy
import time
from enum import Enum
from typing import TYPE_CHECKING, List, Dict

import pygame

from Events import PybEvents
from Events.PybEvents import GUIEvent
from Utilities.AddressFile import AddressFile
from Utilities.Exceptions import MalformedAddressFileError, InvalidComponentTypeError, MalformedProtocolError

if TYPE_CHECKING:
    from Workstation.Workstation import Workstation
    from pygame import Surface
    from Elements.Element import Element

from abc import ABCMeta, abstractmethod

from GUIs import Colors


class GUI:
    __metaclass__ = ABCMeta

    def __init__(self, event: PybEvents.AddTaskEvent, task_gui: Surface, ws: Workstation):
        self.task_gui = task_gui
        self.SF = task_gui.get_width() / 500
        self.ws = ws
        self.components = {}
        self.time_elapsed = 0
        self.time_in_state = 0
        self.state_enter_time = 0
        self.complete = False
        self.chamber = event.chamber
        self.started = False
        self.paused = False
        self.state = None
        self.last_event = None

        task_module = importlib.import_module("Local.Tasks." + event.task_name)
        task = getattr(task_module, event.task_name)
        protocol = event.metadata["protocol"]
        address_file = event.metadata["address_file"]
        component_definition = task.get_components()

        # Get all default values for task constants
        for key, value in task.get_constants().items():
            setattr(self, key, value)

        # Open the provided AddressFile
        comp_index = 0
        if isinstance(address_file, str) and len(address_file) > 0:
            try:
                file_globals = runpy.run_path(address_file, {"AddressFile": AddressFile})
            except:
                raise MalformedAddressFileError
            for cid in file_globals['addresses'].addresses:
                if cid in component_definition:
                    comps = file_globals['addresses'].addresses[cid]
                    for i, comp in enumerate(comps):
                        # Import and instantiate the indicated Component with the provided ID and address
                        component_type = getattr(importlib.import_module("Components." + comp.component_type),
                                                 comp.component_type)
                        if issubclass(component_type, component_definition[cid][i]):
                            component = component_type(None, "{}-{}-{}".format(cid, str(self.chamber),
                                                                               str(i)), comp.component_address)
                            if comp.metadata is not None:
                                component.initialize(comp.metadata)
                            # If the ID has yet to be registered
                            if not hasattr(self, cid):
                                # If the Component is part of a list
                                if len(comps) > 1:
                                    # Create the list and add the Component at the specified index
                                    component_list = [None] * int(len(comps))
                                    component_list[i] = component
                                    setattr(self, cid, component_list)
                                else:  # If the Component is unique
                                    setattr(self, cid, component)
                            else:  # If the Component is part of an already registered list
                                # Update the list with the Component at the specified index
                                component_list = getattr(self, cid)
                                component_list[i] = component
                                setattr(self, cid, component_list)
                            self.components[component.id] = (component, comp_index, comp.source_name)
                            comp_index += 1
                        else:
                            raise InvalidComponentTypeError

        for name in component_definition:
            for i in range(len(component_definition[name])):
                if not hasattr(self, name) or (
                        type(getattr(self, name)) is list and getattr(self, name)[i] is None):
                    component = component_definition[name][i](None, name + "-" + str(self.chamber) + "-" + str(i),
                                                              str(comp_index))
                    if not hasattr(self, name):
                        # If the Component is part of a list
                        if len(component_definition[name]) > 1:
                            # Create the list and add the Component at the specified index
                            component_list = [None] * int(len(component_definition[name]))
                            component_list[i] = component
                            setattr(self, name, component_list)
                        else:  # If the Component is unique
                            setattr(self, name, component)
                    else:  # If the Component is part of an already registered list
                        # Update the list with the Component at the specified index
                        component_list = getattr(self, name)
                        component_list[i] = component
                        setattr(self, name, component_list)
                    self.components[component.id] = (component, comp_index, None)
                    comp_index += 1

        # If a Protocol is provided, replace all indicated variables with the values from the Protocol
        if isinstance(protocol, str) and len(protocol) > 0:
            try:
                file_globals = runpy.run_path(protocol)
            except:
                raise MalformedProtocolError
            for cons in file_globals['protocol']:
                if hasattr(self, cons):
                    setattr(self, cons, file_globals['protocol'][cons])

        # Get all default values for task variables
        self.variable_defaults = task.get_variables()

        self.elements = self.initialize()

    @abstractmethod
    def initialize(self) -> List[Element]:
        raise NotImplementedError

    def draw(self) -> None:
        if self.complete:
            self.task_gui.fill(Colors.green)
        else:
            self.task_gui.fill(Colors.darkgray)
        for el in self.elements:
            el.draw()
        pygame.draw.rect(self.task_gui, Colors.white, self.task_gui.get_rect(), 1)

    def handle_event(self, event: PybEvents.PybEvent) -> None:
        if self.last_event is None:
            dt = 0
        else:
            dt = time.perf_counter() - self.last_event
        self.last_event = time.perf_counter()
        event_type = type(event)
        if event_type == PybEvents.PygameEvent:
            if self.started and not self.paused:
                for el in self.elements:
                    el.handle_event(pygame.event.Event(event.event_type, event.event_dict))
        elif event_type == PybEvents.ComponentUpdateEvent:
            self.components[event.comp_id][0].update(event.value)
        elif event_type == PybEvents.StartEvent:
            self.started = True
            self.time_elapsed = 0
            for key, value in self.variable_defaults.items():
                setattr(self, key, value)
        elif event_type == PybEvents.HeartbeatEvent:
            if self.started and not self.paused:
                self.time_elapsed += dt
                self.time_in_state += dt
        elif event_type == PybEvents.StateEnterEvent:
            self.state = event.name
            self.time_in_state = 0
            self.state_enter_time = event.timestamp
        elif event_type == PybEvents.StopEvent:
            self.last_event = None
            self.started = False
        elif event_type == PybEvents.PauseEvent:
            self.last_event = None
            self.paused = True
        elif event_type == PybEvents.ResumeEvent:
            self.paused = False
        if isinstance(event, PybEvents.TimedEvent) and self.started:
            self.time_elapsed = event.timestamp
            self.time_in_state = event.timestamp - self.state_enter_time

    def start(self):
        self.started = True
        self.time_elapsed = 0
        for key, value in self.variable_defaults.items():
            setattr(self, key, value)

    def log_gui_event(self, event: Enum, metadata: Dict = None):
        metadata = metadata or {}
        self.ws.mainq.send_bytes(self.ws.encoder.encode(GUIEvent(self.chamber, event.name, event.value, metadata=metadata)))
