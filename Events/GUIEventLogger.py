from abc import ABCMeta, abstractmethod
from Events.EventLogger import EventLogger


class GUIEventLogger(EventLogger):
    __metaclass__ = ABCMeta

    @abstractmethod
    def close(self): raise NotImplementedError

    @abstractmethod
    def log_events(self, events): raise NotImplementedError

    @abstractmethod
    def get_widget(self): raise NotImplementedError

