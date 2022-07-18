from enum import Enum

import numpy as np
from Tasks.Task import Task

from source.Events.OEEvent import OEEvent


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
        self.stim.parametrize(0, [1, 3], 180, 1800, np.array([300, -300], [0, 0]), [90, 90])
        self.events.append(OEEvent("startRecording", self.cur_time - self.start_time, {"pre": "ClosedLoop"}))
        super(ERP, self).start()

    def main_loop(self):
        super().main_loop()
        if self.state == self.States.START_RECORD:
            if self.cur_time - self.entry_time > self.record_lockout:
                self.change_state(self.States.ERP)
        if self.cur_time - self.last_pulse_time > self.min_pulse_separation and self.cur_time - self.entry_time > self.closed_loop_duration * 60:
            self.change_state(self.States.STOP_RECORD)
            self.events.append(OEEvent("stopRecording", self.cur_time - self.start_time))
        else:
            if self.cur_time - self.last_pulse_time > self.pulse_sep and self.pulse_count == self.npulse:
                self.change_state(self.States.STOP_RECORD)
            elif self.cur_time - self.last_pulse_time > self.pulse_sep:
                self.last_pulse_time = self.cur_time
                self.stim.start(0)
                self.pulse_count += 1

    def get_variables(self):
        return {
            'record_lockout': 4,
            'npulse': 40,
            'pulse_sep': 4,
        }

    def is_complete(self):
        return self.state == self.States.STOP_RECORD and self.cur_time - self.entry_time > self.record_lockout
