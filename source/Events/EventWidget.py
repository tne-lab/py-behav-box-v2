from PyQt5.QtCore import pyqtSlot, pyqtSignal

from Events import PybEvents
from Events.LoggerEvent import LoggerEvent
from Events.Widget import Widget


class EventWidget(Widget):
    emitter = pyqtSignal(PybEvents.PybEvent)

    def __init__(self, name: str):
        super(EventWidget, self).__init__(name)
        self.event_count = 0
        self.emitter.connect(lambda event: self.handle_event(event))

    @pyqtSlot()
    def handle_event(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.StartEvent) and "sub_task" not in event.metadata:
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
