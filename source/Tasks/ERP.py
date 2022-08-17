from enum import Enum

import numpy as np
from Tasks.Task import Task

from Events.OEEvent import OEEvent
from Events.InputEvent import InputEvent


class ERP(Task):
    class States(Enum):
        START_RECORD = 0
        ERP = 1
        STOP_RECORD = 2

    class Inputs(Enum):
        ERP_STIM = 0

    def __init__(self, *args):
        super().__init__(*args)
        self.last_pulse_time = 0
        self.pulse_count = 0
        self.stim_last = False
        self.complete = False

    def start(self):
        self.state = self.States.START_RECORD
        self.stim.parametrize(0, 1, 180, 180, np.array(([[1, -1]])), [90, 90])
        if self.ephys:
            self.events.append(OEEvent(self, "startRecording", {"pre": "ClosedLoop"}))
        super(ERP, self).start()

    def main_loop(self):
        super().main_loop()
        if self.state == self.States.START_RECORD:
            if self.time_in_state() > self.record_lockout:
                self.change_state(self.States.ERP)
        elif self.state == self.States.ERP:
            if self.cur_time - self.last_pulse_time > self.pulse_sep and self.pulse_count == self.npulse:
                self.change_state(self.States.STOP_RECORD)
                if self.ephys:
                    self.events.append(OEEvent(self, "stopRecording"))
            elif self.cur_time - self.last_pulse_time > self.pulse_sep:
                self.last_pulse_time = self.cur_time
                self.stim.start(0)
                self.pulse_count += 1
                self.events.append(InputEvent(self, self.Inputs.ERP_STIM))

    def get_variables(self):
        return {
            'ephys': False,
            'record_lockout': 4,
            'npulse': 5,
            'pulse_sep': 4,
        }

    def is_complete(self):
        return self.state == self.States.STOP_RECORD and self.time_in_state() > self.record_lockout
