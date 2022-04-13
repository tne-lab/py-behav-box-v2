from Events.GUIEventLogger import GUIEventLogger
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent
from Events.InitialStateEvent import InitialStateEvent
from Events.FinalStateEvent import FinalStateEvent
from Workstation.ScrollLabel import ScrollLabel


class TextEventLogger(GUIEventLogger):

    def __init__(self):
        super(TextEventLogger, self).__init__()
        self.event_log = ScrollLabel()
        self.event_log.setMaximumHeight(100)
        self.event_log.setMinimumHeight(100)
        self.event_log.verticalScrollBar().rangeChanged.connect(
            lambda: self.event_log.verticalScrollBar().setValue(self.event_log.verticalScrollBar().maximum()))

    def log_events(self, events):
        cur_text = self.event_log.text()
        if len(events) > 0 and self.event_count > 0:
            cur_text += "\n"
        for i in range(len(events)):
            e = events[i]
            self.event_count += 1
            if isinstance(e, InitialStateEvent):
                cur_text += "{},{},Entry,{},{},{}".format(self.event_count, e.entry_time,
                                                          e.initial_state.value, e.initial_state.name, str(e.metadata))
            elif isinstance(e, FinalStateEvent):
                cur_text += "{},{},Exit,{},{},{}".format(self.event_count, e.entry_time,
                                                         e.final_state.value, e.final_state.name, str(e.metadata))
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
            self.event_log.setText(cur_text)

    def get_widget(self):
        return self.event_log

    def start(self):
        super(TextEventLogger, self).start()
        self.event_log.setText("")

    def close(self):
        pass
