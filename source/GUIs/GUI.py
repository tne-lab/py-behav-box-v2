from __future__ import annotations
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from Events.Event import Event
    from Tasks.Task import Task
    from pygame import Surface
    from Elements.Element import Element

from abc import ABCMeta, abstractmethod

from GUIs import Colors


class GUI:
    __metaclass__ = ABCMeta

    def __init__(self, task_gui: Surface, task: Task):
        self.task_gui = task_gui
        self.SF = task_gui.get_width() / 500
        self.task = task

    def draw(self) -> None:
        if self.task.is_complete():
            self.task_gui.fill(Colors.green)
        else:
            self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    @abstractmethod
    def get_elements(self) -> List[Element]:
        raise NotImplementedError

    def handle_events(self, events: List[Event]) -> None:
        for event in events:
            for el in self.get_elements():
                el.handle_event(event)
