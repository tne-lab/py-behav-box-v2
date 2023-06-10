from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Events.LoggerEvent import LoggerEvent

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

    def __init__(self, output_folder: str = None):
        super().__init__()
        self.output_folder = output_folder
        self.log_file = None

    @abstractmethod
    def get_file_path(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def log_event(self, event: LoggerEvent) -> None:
        pass
        self.log_file.flush()  # Need a better solution for regular saving

    def begin(self) -> None:
        super(FileEventLogger, self).begin()
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.log_file = open(self.get_file_path(), "w")

    def stop(self) -> None:
        if self.log_file is not None:
            self.log_file.close()
