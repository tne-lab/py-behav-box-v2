from enum import Enum

from Tasks.Task import Task
from Components.TimedToggle import TimedToggle


class FoodDispenserTest(Task):
    """@DynamicAttrs"""
    class States(Enum):
        WAIT = 0
        ACTIVE = 1

    @staticmethod
    def get_components():
        return {
            "food": [TimedToggle]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'dispense_time': 0.7,
            'delay': 1,
            'n_dispense': 5
        }

    def init_state(self):
        return self.States.WAIT

    def WAIT(self):
        if self.time_in_state() > self.delay:
            self.food.toggle(self.dispense_time)
            self.change_state(self.States.ACTIVE)

    def ACTIVE(self):
        if self.time_in_state() > self.dispense_time:
            self.change_state(self.States.WAIT)

    def is_complete(self):
        return self.food.count == self.n_dispense
