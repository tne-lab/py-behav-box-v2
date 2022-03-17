from Events.EventLogger import EventLogger
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent
from Events.InitialStateEvent import InitialStateEvent


class GUIEventLogger(EventLogger):

    def __init__(self, event_logger):
        super(GUIEventLogger, self).__init__()
        self.event_logger = event_logger

    def log_events(self, events):
        cur_text = self.event_logger.text()
        if len(events) > 0 and self.event_count > 0:
            cur_text += "\n"
        for i in range(len(events)):
            e = events[i]
            self.event_count += 1
            if isinstance(e, InitialStateEvent):
                cur_text += "{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                          e.initial_state.value, e.initial_state.name, str(e.metadata))
            elif isinstance(e, StateChangeEvent):
                cur_text += "{},{},Exit,{},{},{}\n".format(self.event_count, e.entry_time,
                                                           e.initial_state.value, e.initial_state.name, str(e.metadata))
                self.event_count += 1
                cur_text += "{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                          e.new_state.value, e.new_state.name, str(None))
            elif isinstance(e, InputEvent):
                cur_text += "{},{},Input,{},{},{}".format(self.event_count, e.entry_time,
                                                          e.input_event.value, e.input_event.name, str(e.metadata))
            if i < len(events) - 1:
                cur_text += "\n"
        if len(events) > 0:
            self.event_logger.setText(cur_text)

    def close(self):
        pass
