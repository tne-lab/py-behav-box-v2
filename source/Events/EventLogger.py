from abc import ABCMeta, abstractmethod


class EventLogger:
    __metaclass__ = ABCMeta
    """
    Abstract class defining the base requirements for an event logging system. Event loggers parse Event objects.

    Methods
    -------
    start()
        Starts the event logger
    close()
        Closes the event logger
    log_events(events)
        Handle each event in the input Event list
    """

    def __init__(self):
        self.event_count = 0

    def start(self):
        self.event_count = 0

    def close(self):
        pass

    def log_event(self, events):
        pass
