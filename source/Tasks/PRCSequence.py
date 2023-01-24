from enum import Enum

from Tasks.TaskSequence import TaskSequence
from Tasks.Raw import Raw
from Tasks.ClosedLoop import ClosedLoop

class PRCSequence(TaskSequence):
    """@DynamicAttrs"""
    class States(Enum):
        PRE_BASELINE = 0 
        ON_EPOCH = 1
        OFF_EPOCH = 2
        POST_BASELINE = 3

    @staticmethod
    def get_tasks():
        return [Raw, ClosedLoop]

    def get_constants(self):
        return {
            "num_trials": 10,
            "pre_baseline_protocol": None,
            "on_epoch_protocol": None,
            "off_epoch_protocol": None,
            "post_baseline_protocol": None
        }

    def get_variables(self):
        return {
            "cur_trial": 0
        }
    
    def start(self):
        self.fan.toggle(True)
        self.house_light.toggle(True)

    def stop(self):
        self.fan.toggle(False)
        self.house_light.toggle(False)

    def init_state(self):
        return self.States.PRE_BASELINE

    def init_sequence(self):
        return Raw, self.pre_baseline_protocol

    def PRE_BASELINE(self):
        if self.cur_task.is_complete():
            self.switch_task(ClosedLoop, self.States.ON_EPOCH, self.on_epoch_protocol)

    def ON_EPOCH(self):
        if self.cur_task.is_complete():
            self.switch_task(Raw, self.States.OFF_EPOCH, self.off_epoch_protocol)

    def OFF_EPOCH(self):
        if self.cur_task.is_complete():
            if self.cur_trial < self.num_trials:
                self.switch_task(ClosedLoop, self.States.ON_EPOCH, self.on_epoch_protocol)
                self.cur_trial += 1
            else:
                self.switch_task(Raw, self.States.POST_BASELINE, self.post_baseline_protocol)

    def is_complete(self):
        return self.state == self.States.POST_BASELINE and self.cur_task.is_complete()

    