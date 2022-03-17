from Events.EventLogger import EventLogger
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent


class ConsoleLogger(EventLogger):

    def __init__(self):
        super().__init__()
        self.event_count = 0

    def log_events(self, events):
        for e in events:
            if isinstance(e, StateChangeEvent):
                self.event_count += 1
                print("{},{},Exit,{},{},{}\n".format(self.event_count, e.entry_time,
                                                     e.initial_state.value, e.initial_state.name, str(e.metadata)))
                self.event_count += 1
                print("{},{},Entry,{},{},{}\n".format(self.event_count, e.entry_time,
                                                      e.new_state.value, e.new_state.name, str(None)))
            elif isinstance(e, InputEvent):
                self.event_count += 1
                print("{},{},Input,{},{},{}\n".format(self.event_count, e.entry_time,
                                                      e.input_event.value, e.input_event.name, str(e.metadata)))

    def close(self):
        pass
