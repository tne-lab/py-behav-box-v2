from enum import Enum

from Components.AnalogInput import AnalogInput
from Components.BinaryInput import BinaryInput
from Tasks.Task import Task
from Components.Toggle import Toggle


class OSCSTest(Task):
    """@DynamicAttrs"""
    class States(Enum):
        ACTIVE = 0

    @staticmethod
    def get_components():
        return {
            "dout": [Toggle],
            "din": [BinaryInput],
            "ain": [AnalogInput],
            "gpioout": [Toggle],
            "gpioin": [BinaryInput]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'duration': 1
        }

    def init_state(self):
        return self.States.ACTIVE

    def start(self):
        self.dout.toggle(True)
        self.gpioout.toggle(True)

    def stop(self):
        self.dout.toggle(False)
        self.gpioout.toggle(False)

    def main_loop(self) -> None:
        self.din.check()
        self.gpioin.check()
        self.ain.check()

    def is_complete(self):
        return self.time_elapsed() > self.duration * 60
