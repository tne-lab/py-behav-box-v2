from enum import Enum

from Tasks.Task import Task


class DPALHabituation1(Task):
    class States(Enum):
        ACTIVE = 0

    class Inputs(Enum):
        INIT_ENTERED = 0
        INIT_EXIT = 1
        FRONT_TOUCH = 2
        MIDDLE_TOUCH = 3
        REAR_TOUCH = 4
        ERROR_TOUCH = 5

    def __init__(self, chamber, source, address_file, protocol):
        super().__init__(chamber, source, address_file, protocol)
        self.fan.toggle(True)
        self.state = self.States.ACTIVE

    def get_variables(self):
        return {
            'duration': 10
        }

    def is_complete(self):
        return self.cur_time - self.start_time > self.duration * 60
