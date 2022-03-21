from abc import ABCMeta, abstractmethod
from Events.EventLogger import EventLogger
from Events.InputEvent import InputEvent
from Events.StateChangeEvent import StateChangeEvent
from Utilities.dictionary_to_save_string import dictionary_to_save_string
import os


class FileEventLogger(EventLogger):
    __metaclass__ = ABCMeta

    def __init__(self, output_folder):
        super().__init__()
        self.output_folder = output_folder
        self.log_file = None

    @abstractmethod
    def get_file_path(self): raise NotImplementedError

    @abstractmethod
    def log_events(self, events): raise NotImplementedError

    def start(self):
        super(FileEventLogger, self).start()
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.log_file = open(self.get_file_path(), "w")

    def close(self):
        self.log_file.close()
