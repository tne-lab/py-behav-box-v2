from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Events.Event import Event

import time
import math

from Events.FileEventLogger import FileEventLogger
from Events.InitialStateEvent import InitialStateEvent
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent
from Events.FinalStateEvent import FinalStateEvent
from Utilities.dictionary_to_save_string import dictionary_to_save_string


class CSVEventLogger(FileEventLogger):

    def get_file_path(self) -> str:
        return "{}{}.csv".format(self.output_folder, math.floor(time.time() * 1000))

    def start(self) -> None:
        super(CSVEventLogger, self).start()
        # self.log_file.write("Subject,{}".format(self.task.))
        self.log_file.write("Trial,Time,Type,Code,State,Metadata\n")

    def log_events(self, events: list[Event]) -> None:
        for e in events:
            self.event_count += 1
            if isinstance(e, InitialStateEvent):
                self.log_file.write("{},{},Entry,{},{},{}\n".format(self.event_count, e.entry_time,
                                                                    e.initial_state.value, e.initial_state.name,
                                                                    str(e.metadata)))
            elif isinstance(e, FinalStateEvent):
                self.log_file.write("{},{},Exit,{},{},{}\n".format(self.event_count, e.entry_time,
                                                                   e.final_state.value, e.final_state.name,
                                                                   str(e.metadata)))
            elif isinstance(e, StateChangeEvent):
                self.log_file.write("{},{},Exit,{},{},{}\n".format(self.event_count, e.entry_time,
                                                                   e.initial_state.value, e.initial_state.name,
                                                                   dictionary_to_save_string(e.metadata)))
                self.event_count += 1
                self.log_file.write("{},{},Entry,{},{},{}\n".format(self.event_count, e.entry_time,
                                                                    e.new_state.value, e.new_state.name, None))
            elif isinstance(e, InputEvent):
                self.log_file.write("{},{},Input,{},{},{}\n".format(self.event_count, e.entry_time,
                                                                    e.input_event.value, e.input_event.name,
                                                                    dictionary_to_save_string(e.metadata)))
        super().log_events(events)
