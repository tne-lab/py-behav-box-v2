from enum import Enum

import numpy as np
from Tasks.Task import Task
from Components.BinaryInput import BinaryInput
from Components.Stimmer import Stimmer
from Events.InputEvent import InputEvent

from Events.OEEvent import OEEvent


class ClosedLoop(Task):
    """@DynamicAttrs"""
    class States(Enum):
        START_RECORD = 0
        CLOSED_LOOP = 1
        STOP_RECORD = 2

    class Inputs(Enum):
        STIM = 0
        SHAM = 1

    @staticmethod
    def get_components():
        return {
            'threshold': [BinaryInput],
            'stim': [Stimmer],
            'sham': [Stimmer]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'record_lockout': 4,
            'duration': 30,
            'min_pulse_separation': 2,
            'stim_dur': 180,
            'period': 180,
            'amps': ([[1, -1]]),
            'pws': [90, 90]
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            'last_pulse_time': 0,
            'pulse_count': 0,
            'stim_last': False,
            'complete': False,
            'thr': None
        }

    def init_state(self):
        return self.States.START_RECORD

    def start(self):
        self.stim.parametrize(0, 1, self.stim_dur, self.period, np.array(self.amps), self.pws)
        self.sham.parametrize(0, 1, self.stim_dur, self.period, np.array(self.amps), self.pws)
        self.events.append(OEEvent(self, "startRecording", {"pre": "ClosedLoop"}))

    def handle_input(self) -> None:
        self.thr = self.threshold.check()

    def START_RECORD(self):
        if self.time_in_state() > self.record_lockout:
            self.change_state(self.States.CLOSED_LOOP)

    def CLOSED_LOOP(self):
        if self.cur_time - self.last_pulse_time > self.min_pulse_separation and self.time_in_state() > self.duration * 60:
            self.change_state(self.States.STOP_RECORD)
            self.events.append(OEEvent(self, "stopRecording"))
        else:
            if self.cur_time - self.last_pulse_time > self.min_pulse_separation:
                if self.thr == BinaryInput.ENTERED:
                    if not self.stim_last:
                        self.events.append(InputEvent(self, self.Inputs.STIM))
                        self.stim.start(0)
                        self.pulse_count += 1
                    else:
                        self.events.append(InputEvent(self, self.Inputs.SHAM))
                        self.sham.start(0)
                    self.stim_last = not self.stim_last

    def is_complete(self):
        return self.state == self.States.STOP_RECORD and self.time_in_state() > self.record_lockout
