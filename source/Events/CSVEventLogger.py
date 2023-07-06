from __future__ import annotations

import collections
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Events.LoggerEvent import LoggerEvent

import time
import math

from Events.FileEventLogger import FileEventLogger


class CSVEventLogger(FileEventLogger):

    def get_file_path(self) -> str:
        return "{}{}.csv".format(self.output_folder, math.floor(time.time() * 1000))

    def start(self) -> None:
        super().start()
        self.log_file.write("Subject,{}".format(self.task.metadata["subject"])+"\n")
        self.log_file.write("Task,{}".format(type(self.task).__name__)+"\n")
        self.log_file.write("Chamber,{}".format(self.task.metadata["chamber"] + 1)+"\n")
        self.log_file.write("Protocol,{}".format(self.task.metadata["protocol"])+"\n")
        self.log_file.write("AddressFile,{}".format(self.task.metadata["address_file"])+"\n\n")
        self.log_file.write("Trial,Time,Type,Code,State,Metadata\n")

    def log_events(self, le: collections.deque[LoggerEvent]) -> None:
        for event in le:
            self.event_count += 1
            self.log_file.write(self.format_event(event, type(event.event).__name__))
        super().log_events(le)
