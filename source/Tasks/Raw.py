from enum import Enum

from Tasks.Task import Task


class Raw(Task):
    class States(Enum):
        ACTIVE = 0

    def __init__(self, *args):
        super().__init__(*args)
        self.fan.toggle(True)
        self.state = self.States.ACTIVE

    def get_variables(self):
        return {
            'duration': 10/60
        }

    def is_complete(self):
        return self.cur_time - self.start_time > self.duration * 60
