from enum import Enum

from Tasks.Task import Task


class DPALHabituation1(Task):
    class States(Enum):
        ACTIVE = 0

    def start(self):
        self.state = self.States.ACTIVE
        self.fan.toggle(True)
        super(DPALHabituation1, self).start()

    def get_variables(self):
        return {
            'duration': 10
        }

    def is_complete(self):
        return self.time_elapsed() > self.duration * 60
