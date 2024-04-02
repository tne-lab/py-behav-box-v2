import importlib
import os
from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing import Process
from multiprocessing.connection import Connection
from typing import List, Dict, Tuple, Any

import msgspec
import pandas as pd

from pybehave.Events import PybEvents


class Validator(ABC):
    class TaskStatus(Enum):
        COMPLETE: 0
        INCOMPLETE: 1
        ERROR: 2

    class TestStatus(Enum):
        PASSED: 0
        FAILED: 1
        ERROR: 2

    @abstractmethod
    def validate(self, event_table: pd.DataFrame, header: Dict) -> Tuple[TaskStatus, Dict[str, Any], Dict[str, Tuple[TestStatus, Any, Any]]]:
        """ Processes the saved event information and validates it

        Parameters
        ----------
        event_table
        header

        Returns
        -------
        Tuple[Enum, Dict, Dict]
            tuple containing the status of the validation, a dictionary of metrics, and a dictionary of test results
        """
        raise NotImplementedError


class ValidatorProcess(Process):
    def __init__(self, vq: Connection):
        super().__init__()
        self.vq = vq
        self.decoder = None
        self.encoder = None

    def run(self):
        self.decoder = msgspec.msgpack.Decoder(type=List[PybEvents.subclass_union(PybEvents.PybEvent)],
                                               dec_hook=PybEvents.dec_hook, ext_hook=PybEvents.ext_hook)
        self.encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)
        while True:
            events = self.decoder.decode(self.vq.recv_bytes())
            for event in events:
                if isinstance(event, PybEvents.ValidatorEvent):
                    try:
                        # Import the logger related to the event
                        logger_class = getattr(importlib.import_module("pybehave.Events." + event.logger), event.logger)
                        # Load the data previously saved by the logger
                        event_table, header = logger_class.load_data(event.path)
                        # Import the task associated with the data
                        task = getattr(importlib.import_module("Local.Tasks." + header['Task']), header['Task'])
                        # Generate the dictionary of constants for the task
                        constants = task.get_constants()
                        # Import the validator associated with this task
                        validator = getattr(importlib.import_module("Local.Validators." + header['Task'] + 'Validator'), header['Task'] + 'Validator')
                        # Validate the data saved for the task
                        status, measures, test_results = validator.validate(event_table, header)
                        # Create the validation file
                        folder, file_name = os.path.split(event.path)
                        with open(folder + '/' + file_name.split('.')[0] + '_validation.txt', 'w') as f:
                            f.write('Status: ' + status.value + '\n\n')
                            f.write('Measures:\n')
                            for name, metric in measures.items():
                                f.write(name + ': ' + str(metric) + '\n')
                            f.write('\n')
                            f.write('Test Results:\n')
                            for name, test in test_results.items():
                                if test[0] == Validator.TestStatus.PASSED:
                                    f.write(name + ': Passed\n')
                                elif test[0] == Validator.TestStatus.FAILED:
                                    f.write(name + f': Failed, Expected {test[1]} found {test[2]}\n')
                    except ModuleNotFoundError:
                        pass
                elif isinstance(event, PybEvents.CloseValidatorEvent):
                    return
