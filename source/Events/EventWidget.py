from abc import abstractmethod

from Events import PybEvents
from Events.LoggerEvent import LoggerEvent
from Events.Widget import Widget


class EventWidget(Widget):

    def __init__(self, name: str):
        super(EventWidget, self).__init__(name)
        self.event_count = 0

    def handle_event(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StartEvent):
            self.start_()
        elif isinstance(event, PybEvents.StopEvent):
            self.stop_()

    def start_(self):
        self.event_count = 0
        self.start()

    def start(self):
        pass

    def stop_(self):
        self.stop()

    def stop(self):
        pass

    def format_event(self, le: LoggerEvent, event_type: str):
        return "{},{},{},{},{},\"{}\"".format(self.event_count, le.entry_time, event_type,
                                              str(le.eid), le.name,
                                              str(le.event.metadata))
