from enum import Enum

from Components.AnalogInput import AnalogInput
from Components.AnalogOutput import AnalogOutput
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
            "ain": [AnalogInput, AnalogInput],
            "gpioout": [Toggle],
            "gpioin": [BinaryInput],
            "aout": [AnalogOutput]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'duration': 6
        }

    def init_state(self):
        return self.States.ACTIVE

    def stop(self):
        self.dout.toggle(False)
        self.gpioout.toggle(False)
        self.aout.set(0)

    def main_loop(self) -> None:
        val = self.din.check()
        if val == BinaryInput.ENTERED:
            self.dout.toggle(True)
        elif val == BinaryInput.EXIT:
            self.dout.toggle(False)
        # self.gpioin.check()
        # self.ain.check()
        # self.din.check()
        # if self.time_elapsed() % 1 > 0.5:
        #     self.aout.set(2.5)
        #     self.dout.toggle(False)
        #     self.gpioout.toggle(False)
        # else:
        #     self.aout.set(0)
        #     self.dout.toggle(True)
        #     self.gpioout.toggle(True)

    def is_complete(self):
        return self.time_elapsed() > self.duration * 60
