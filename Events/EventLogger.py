from abc import ABCMeta, abstractmethod


class EventLogger:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.event_count = 0

    @abstractmethod
    def close(self): raise NotImplementedError

    @abstractmethod
    def log_events(self, events): raise NotImplementedError

    def reset(self):
        self.event_count = 0
