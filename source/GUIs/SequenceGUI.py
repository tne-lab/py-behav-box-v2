from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Tasks.Task import Task
    from pygame import Surface
    from Elements.Element import Element

from pygame.event import Event

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
        for el in self.get_elements():
            el.draw()

    @abstractmethod
    def get_elements(self) -> list[Element]:
        raise NotImplementedError

    def get_all_elements(self):
        if self.sub_gui is not None:
            return self.get_elements() + self.sub_gui.get_elements()
        else:
            return self.get_elements()

    def handle_event(self, event: Event) -> bool:
        handled = super(SequenceGUI, self).handle_event(event)
        return handled or (self.sub_gui is not None and self.sub_gui.handle_event(event))
