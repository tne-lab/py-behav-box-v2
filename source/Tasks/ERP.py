from enum import Enum

import numpy as np
from Tasks.Task import Task
from Components.Stimmer import Stimmer

from Events.OEEvent import OEEvent
from Events.InputEvent import InputEvent


class ERP(Task):
    """@DynamicAttrs"""
    class States(Enum):
        START_RECORD = 0
        ERP = 1
        STOP_RECORD = 2

    class Inputs(Enum):
        ERP_STIM = 0

    @staticmethod
    def get_components():
        return {
            'stim': [Stimmer]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'ephys': False,
            'record_lockout': 4,
            'npulse': 5,
            'pulse_sep': 4,
            'stim_dur': 180,
            'period': 180,
            'amps': ([[1, -1]]),
            'pws': [90, 90]
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            "last_pulse_time": 0,
            "pulse_count": 0,
            "stim_last": False,
            "complete": False
        }

    def init_state(self):
        return self.States.START_RECORD

    def start(self):
        self.stim.parametrize(0, 1, self.stim_dur, self.period, np.array(self.amps), self.pws)
        if self.ephys:
            self.events.append(OEEvent(self, "startRecording", {"pre": "ClosedLoop"}))

    def START_RECORD(self):
        if self.time_in_state() > self.record_lockout:
            self.change_state(self.States.ERP)

    def ERP(self):
        if self.cur_time - self.last_pulse_time > self.pulse_sep and self.pulse_count == self.npulse:
            self.change_state(self.States.STOP_RECORD)
            if self.ephys:
                self.events.append(OEEvent(self, "stopRecording"))
        elif self.cur_time - self.last_pulse_time > self.pulse_sep:
            self.last_pulse_time = self.cur_time
            self.stim.start(0)
            self.pulse_count += 1
            self.events.append(InputEvent(self, self.Inputs.ERP_STIM))

    def is_complete(self):
        return self.state == self.States.STOP_RECORD and self.time_in_state() > self.record_lockout
