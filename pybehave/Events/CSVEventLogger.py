from __future__ import annotations

import collections
import os
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pybehave.Events.LoggerEvent import LoggerEvent

import time
import math

from pybehave.Events.FileEventLogger import FileEventLogger


class CSVEventLogger(FileEventLogger):

    def get_file_path(self) -> str:
        return "{}{}.csv".format(self.output_folder, math.floor(time.time() * 1000))

    def start(self) -> None:
        super().start()
        self.log_file.write("Subject,{}".format(self.task.metadata["subject"])+"\n")
        self.log_file.write("Task,{}".format(type(self.task).__name__)+"\n")
        self.log_file.write("Chamber,{}".format(self.task.metadata["chamber"] + 1)+"\n")
        self.log_file.write("Protocol,{}".format(self.task.metadata["protocol"])+"\n")
        self.log_file.write("AddressFile,{}".format(self.task.metadata["address_file"])+"\n")
        if len(self.task.initial_constants) > 0:
            self.log_file.write("SubjectConfiguration\n")
            for key, value in self.task.initial_constants.items():
                self.log_file.write("{},\"{}\"\n".format(key, getattr(self.task, key)))
        self.log_file.write("\n")
        self.log_file.write("Trial,Time,Type,Code,State,Metadata\n")

    def log_events(self, le: collections.deque[LoggerEvent]) -> None:
        for event in le:
            self.event_count += 1
            self.log_file.write(self.format_event(event, type(event.event).__name__))
        super().log_events(le)

    @staticmethod
    def load_data(path):
        header = {}
        skip_lines = 0

        with open(path) as f:
            for line in f:
                skip_lines += 1
                if line == '\n':
                    break
                elif line == 'SubjectConfiguration\n':
                    header['subject_config'] = {}
                else:
                    pair = line.split(',', 1)
                    if 'subject_config' in header:
                        header['subject_config'][pair[0]] = pair[1][:-1]
                    else:
                        header[pair[0]] = pair[1][:-1]

        header['timestamp'] = os.path.split(path)[-1].split('.')[0]
        event_table = pd.read_csv(path, skiprows=skip_lines)
        return event_table, header
