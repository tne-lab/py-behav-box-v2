from abc import ABCMeta, abstractmethod


class EventLogger:
    __metaclass__ = ABCMeta

    @abstractmethod
    def close(self): raise NotImplementedError

    @abstractmethod
    def log_events(self, events): raise NotImplementedError
