from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pygame import Surface
    from Elements.Element import Element
    from Workstation.Workstation import Workstation

from abc import ABCMeta, abstractmethod
import importlib

from Events import PybEvents
from GUIs import Colors
from GUIs.GUI import GUI
from pygame import Surface

class SequenceGUI(GUI):
    __metaclass__ = ABCMeta

    def __init__(self, event: PybEvents.AddTaskEvent, task_gui: Surface, ws: Workstation):
        super(SequenceGUI, self).__init__(event, task_gui, ws)
        self.sub_gui = None
        self.init_event = event
        self.task_gui = task_gui
        self.ws = ws

    def draw(self) -> None:
        if self.complete:
            self.task_gui.fill(Colors.green)
            self.sub_gui = None
        if self.sub_gui is not None:
            self.sub_gui.draw()
        for el in self.elements:
            el.draw()

    @abstractmethod
    def initialize(self) -> list[Element]:
        raise NotImplementedError

    def switch_sub_gui(self, event: PybEvents.StartEvent):
        class_name = event.metadata['sub_task'].split('.')[-1].split("'")[0]
        gui = getattr(importlib.import_module("Local.GUIs." + class_name + "GUI"), class_name + "GUI")
        metadata = event.metadata.copy()
        metadata["protocol"] = event.metadata["protocol"]
        metadata["address_file"] = self.init_event.metadata["address_file"]

        # Make a dummy AddTaskEvent to create the GUI. Task loggers field is unused and can be empty
        dummy_event = PybEvents.AddTaskEvent(event.chamber, class_name, "", metadata=metadata)
        self.sub_gui = gui(dummy_event, self.task_gui, self.ws)

        for key, value in self.sub_gui.variable_defaults.items():
            setattr(self.sub_gui, key, value)
        self.sub_gui.handle_event(event)
        self.sub_gui.time_offset = self.time_elapsed

    def get_all_elements(self):
        if self.sub_gui is not None:
            return self.elements + self.sub_gui.elements
        else:
            return self.elements

    def handle_event(self, event: PybEvents.PybEvent) -> None:
        if isinstance(event, PybEvents.TaskCompleteEvent) and "sequence_complete" in event.metadata:
            self.started = False
        # Don't reset sequence time elapsed on sub-task start events
        elif not (isinstance(event, PybEvents.StartEvent) and "sub_task" in event.metadata):
            super(SequenceGUI, self).handle_event(event)
        # Don't pass sequence component updates to the sub-gui
        if self.sub_gui is not None and not (isinstance(event, PybEvents.ComponentUpdateEvent) and event.comp_id not in self.sub_gui.components):
            self.sub_gui.handle_event(event)
