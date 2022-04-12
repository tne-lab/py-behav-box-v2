from enum import Enum

from Tasks.Task import Task


class DPALHabituation1(Task):
    class States(Enum):
        ACTIVE = 0

    def __init__(self, chamber, source, address_file, protocol):
        super().__init__(chamber, source, address_file, protocol)
        self.fan.toggle(True)
        self.state = self.States.ACTIVE

    def main_loop(self):
        super().main_loop()
        self.events = []

    def get_variables(self):
        return {
            'duration': 10
        }

    def is_complete(self):
        return self.cur_time - self.start_time > self.duration * 60
