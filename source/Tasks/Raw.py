from enum import Enum

from Tasks.Task import Task
from Components.Toggle import Toggle


class Raw(Task):
    """@DynamicAttrs"""
    class States(Enum):
        ACTIVE = 0

    @staticmethod
    def get_components():
        return {
            "fan": [Toggle],
            "house_light": [Toggle]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'duration': 10/60
        }

    def init_state(self):
        return self.States.ACTIVE

    def start(self):
        self.fan.toggle(True)
        self.house_light.toggle(True)

    def stop(self):
        self.fan.toggle(False)
        self.house_light.toggle(False)

    def is_complete(self):
        return self.time_elapsed() > self.duration * 60
