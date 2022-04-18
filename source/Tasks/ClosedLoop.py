from enum import Enum

from Tasks.Task import Task
from source.Components.BinaryInput import BinaryInput
from source.Events.InputEvent import InputEvent


class ClosedLoop(Task):
    class States(Enum):
        ACTIVE = 0

    class Inputs(Enum):
        THRESH_RISING = 0
        THRESH_FALLING = 1

    def __init__(self, chamber, source, address_file, protocol):
        super().__init__(chamber, source, address_file, protocol)
        self.fan.toggle(True)
        self.state = self.States.ACTIVE
        self.activated = False

    def main_loop(self):
        super().main_loop()
        self.events = []
        thr = self.threshold.check()
        if thr == BinaryInput.ENTERED:
            self.events.append(InputEvent(self.Inputs.THRESH_RISING, self.cur_time - self.start_time))
            self.activated = True
        elif thr == BinaryInput.EXIT:
            self.events.append(InputEvent(self.Inputs.THRESH_FALLING, self.cur_time - self.start_time))
            self.activated = False

    def get_variables(self):
        return {
            'duration': 10
        }

    def is_complete(self):
        return self.cur_time - self.start_time > self.duration * 60
