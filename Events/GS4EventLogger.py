from Events.EventLogger import EventLogger
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent


class GS4EventLogger(EventLogger):

    def __init__(self, file_path):
        self.log_file = open(file_path)
        self.event_count = 0

    def log_events(self, events):
        for e in events:
            if isinstance(e, StateChangeEvent):
                self.event_count += 1
                self.log_file.write("{},{},Exit,{},{}\n".format(self.event_count, e.entry_time,
                                                                 e.initial_state.value, e.initial_state.name))
                self.event_count += 1
                self.log_file.write("{},{},Entry,{},{}\n".format(self.event_count, e.entry_time,
                                                                e.new_state.value, e.new_state.name))
            elif isinstance(e, InputEvent):
                self.event_count += 1
                self.log_file.write("{},{},Input,{},{}\n".format(self.event_count, e.entry_time,
                                                                 e.input_event.value, e.input_event.name))

    def close(self):
        self.log_file.close()
