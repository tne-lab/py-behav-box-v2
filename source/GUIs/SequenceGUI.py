from abc import ABCMeta, abstractmethod
from GUIs.GUI import GUI


class SequenceGUI(GUI):
    __metaclass__ = ABCMeta

    def __init__(self, task_gui, task):
        super(SequenceGUI, self).__init__(task_gui, task)
        self.sub_gui = None

    def draw(self):
        if self.sub_gui is not None:
            self.sub_gui.draw()

    @abstractmethod
    def get_elements(self):
        raise NotImplementedError

    def handle_events(self, events):
        super(SequenceGUI, self).handle_events(events)
        self.sub_gui.handle_events(events)
