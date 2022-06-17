from enum import Enum
import time
from Tasks.Task import Task
from source.Components.BinaryInput import BinaryInput
from source.Events.InputEvent import InputEvent
from source.Events.OEEvent import OEEvent


class ClosedLoop(Task):
    class States(Enum):
        PRE_RAW = 0
        PRE_ERP = 1
        CLOSED_LOOP = 2
        POST_ERP = 3
        POST_RAW = 4
        START_RECORD = 5
        STOP_RECORD = 6

    class Inputs(Enum):
        STIM = 0
        SHAM = 1

    def __init__(self, chamber, source, address_file, protocol):
        super().__init__(chamber, source, address_file, protocol)
        self.state = self.States.START_RECORD
        self.next_state = self.States.PRE_RAW
        self.last_pulse_time = 0
        self.pulse_count = 0
        self.stim_last = False
        self.complete = False
        self.recording_started = False

    def start(self):
        super(ClosedLoop, self).start()
        self.stim.parametrize(0, 1, 3, 180, 180, [300, -300], [0, 0], [90, 90])

    def main_loop(self):
        super().main_loop()
        thr = self.threshold.check()
        if self.state == self.States.START_RECORD:
            if not self.recording_started:
                self.recording_started = True
                self.events.append(OEEvent("startRecording", self.cur_time - self.start_time, {"pre": self.next_state.name}))
            if self.cur_time - self.entry_time > self.record_lockout:
                self.change_state(self.next_state)
        elif self.state == self.States.STOP_RECORD:
            if self.recording_started:
                self.recording_started = False
                self.events.append(OEEvent("stopRecording", self.cur_time - self.start_time))
            if self.cur_time - self.entry_time > self.record_lockout:
                if self.next_state is not None:
                    self.change_state(self.States.START_RECORD)
                else:
                    self.complete = True
        elif self.state == self.States.PRE_RAW:
            if self.cur_time - self.entry_time > self.pre_raw_duration*60:
                self.next_state = self.States.PRE_ERP
                self.change_state(self.States.STOP_RECORD)
        elif self.state == self.States.PRE_ERP:
            if time.time() - self.last_pulse_time > self.pre_erp_pulse_sep and self.pulse_count == self.pre_erp_npulse:
                self.pulse_count = 0
                self.next_state = self.States.CLOSED_LOOP
                self.change_state(self.States.STOP_RECORD)
            elif time.time() - self.last_pulse_time > self.pre_erp_pulse_sep:
                self.last_pulse_time = time.time()
                self.ttl.pulse()
                self.pulse_count += 1
        elif self.state == self.States.CLOSED_LOOP:
            if time.time() - self.last_pulse_time > self.min_pulse_separation and time.time() - self.entry_time > self.closed_loop_duration*60:
                self.next_state = self.States.POST_ERP
                self.change_state(self.States.STOP_RECORD)
            else:
                if time.time() - self.last_pulse_time > self.min_pulse_separation:
                    if thr == BinaryInput.ENTERED:
                        if not self.stim_last:
                            self.events.append(InputEvent(self.Inputs.STIM, self.cur_time - self.start_time))
                            self.ttl.pulse()
                        else:
                            self.events.append(InputEvent(self.Inputs.SHAM, self.cur_time - self.start_time))
                        self.stim_last = not self.stim_last
        elif self.state == self.States.POST_ERP:
            if time.time() - self.last_pulse_time > self.post_erp_pulse_sep and self.pulse_count == self.post_erp_npulse:
                self.next_state = self.States.PRE_RAW
                self.change_state(self.States.STOP_RECORD)
            elif time.time() - self.last_pulse_time > self.post_erp_pulse_sep:
                self.last_pulse_time = time.time()
                self.ttl.pulse()
                self.pulse_count += 1
        elif self.state == self.States.POST_RAW:
            if self.cur_time - self.entry_time > self.post_raw_duration*60:
                self.next_state = None
                self.change_state(self.States.STOP_RECORD)

    def get_variables(self):
        return {
            'record_lockout': 4,
            'pre_raw_duration': 5,
            'pre_erp_npulse': 40,
            'pre_erp_pulse_sep': 4,
            'closed_loop_duration': 30,
            'min_pulse_separation': 2,
            'post_erp_npulse': 40,
            'post_erp_pulse_sep': 4,
            'post_raw_duration': 5
        }

    def is_complete(self):
        return self.complete
