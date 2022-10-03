from abc import ABCMeta, abstractmethod
from GUIs import Colors


class GUI:
    __metaclass__ = ABCMeta

    def __init__(self, task_gui, task):
        self.task_gui = task_gui
        self.SF = task_gui.get_width() / 500
        self.task = task

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    @abstractmethod
    def get_elements(self):
        raise NotImplementedError

    def handle_events(self, events):
        for event in events:
            for el in self.get_elements():
                el.handle_event(event)
