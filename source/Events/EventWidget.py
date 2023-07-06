from abc import abstractmethod

from Events import PybEvents
from Events.LoggerEvent import LoggerEvent
from Events.Widget import Widget


class EventWidget(Widget):

    def __init__(self, name: str):
        super(EventWidget, self).__init__(name)
        self.event_count = 0

    @abstractmethod
    def handle_event(self, event: PybEvents.PybEvent):
        pass

    def start_(self):
        self.event_count = 0

    def format_event(self, le: LoggerEvent, event_type: str):
        return "{},{},{},{},{},\"{}\"".format(self.event_count, le.entry_time, event_type,
                                              str(le.eid), le.name,
                                              str(le.event.metadata))
