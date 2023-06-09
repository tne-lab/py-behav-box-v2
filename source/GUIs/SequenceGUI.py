from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Events.LoggerEvent import LoggerEvent
    from Tasks.Task import Task
    from pygame import Surface
    from Elements.Element import Element

from abc import ABCMeta, abstractmethod

from GUIs.GUI import GUI


class SequenceGUI(GUI):
    __metaclass__ = ABCMeta

    def __init__(self, task_gui: Surface, task: Task):
        super(SequenceGUI, self).__init__(task_gui, task)
        self.sub_gui = None

    def draw(self) -> None:
        if self.sub_gui is not None:
            self.sub_gui.draw()

    @abstractmethod
    def get_elements(self) -> list[Element]:
        raise NotImplementedError

    def handle_events(self, events: list[LoggerEvent]) -> None:
        super(SequenceGUI, self).handle_events(events)
        self.sub_gui.handle_events(events)
