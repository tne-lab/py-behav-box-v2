from abc import ABCMeta, abstractmethod
from Events.EventLogger import EventLogger
import os


class FileEventLogger(EventLogger):
    __metaclass__ = ABCMeta
    """
    Abstract class defining the base requirements for an EventLogger that logs Event objects to a file on disk.

    Methods
    -------
    start()
        Opens the file
    close()
        Closes the file
    log_events(events)
        Handle saving of each Event in the input list to the file
    get_file_path()
        Returns the 
    """

    def __init__(self, output_folder):
        super().__init__()
        self.output_folder = output_folder
        self.log_file = None

    @abstractmethod
    def get_file_path(self): raise NotImplementedError

    @abstractmethod
    def log_events(self, events):
        self.log_file.flush()

    def start(self):
        super(FileEventLogger, self).start()
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.log_file = open(self.get_file_path(), "w")

    def close(self):
        if self.log_file is not None:
            self.log_file.close()
