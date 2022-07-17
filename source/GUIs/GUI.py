from abc import ABCMeta, abstractmethod


class GUI:
    __metaclass__ = ABCMeta

    def __init__(self, task_gui, task):
        self.task_gui = task_gui
        self.SF = task_gui.get_width() / 500
        self.task = task

    @abstractmethod
    def draw(self):
        raise NotImplementedError

    @abstractmethod
    def get_elements(self):
        raise NotImplementedError

    def handle_events(self, events):
        for event in events:
            for el in self.get_elements():
                el.handle_event(event)
