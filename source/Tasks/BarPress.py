from enum import Enum

import random

from Components.BinaryInput import BinaryInput
from Components.Toggle import Toggle
from Components.TimedToggle import TimedToggle
from Components.Video import Video
from Events.InputEvent import InputEvent
from Tasks.Task import Task


class BarPress(Task):
    """@DynamicAttrs"""
    class States(Enum):
        REWARD_AVAILABLE = 0
        REWARD_UNAVAILABLE = 1

    class Inputs(Enum):
        LEVER_PRESSED = 0
        LEVER_DEPRESSED = 1

    @staticmethod
    def get_components():
        return {
            'food_lever': [BinaryInput],
            'cage_light': [Toggle],
            'food': [TimedToggle],
            'fan': [Toggle],
            'lever_out': [Toggle],
            'food_light': [Toggle],
            'cam': [Video]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'duration': 40,
            'reward_lockout': False,
            'reward_lockout_min': 25,
            'reward_lockout_max': 35,
            'dispense_time': 0.7
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            'lockout': 0,
            'presses': 0,
            'pressed': False
        }

    def init_state(self):
        return self.States.REWARD_AVAILABLE

    def start(self):
        self.cage_light.toggle(True)
        self.cam.start()
        self.fan.toggle(True)
        self.lever_out.toggle(True)
        self.food_light.toggle(True)

    def stop(self):
        self.food_light.toggle(False)
        self.cage_light.toggle(False)
        self.fan.toggle(False)
        self.lever_out.toggle(False)
        self.cam.stop()

    def handle_input(self) -> None:
        food_lever = self.food_lever.check()
        self.pressed = False
        if food_lever == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.LEVER_PRESSED))
            self.pressed = True
            self.presses += 1
        elif food_lever == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.LEVER_DEPRESSED))

    def REWARD_AVAILABLE(self):
        if self.pressed:
            self.food.toggle(self.dispense_time)
            if self.reward_lockout:
                self.lockout = self.reward_lockout_min + random.random() * (
                            self.reward_lockout_max - self.reward_lockout_min)
                self.change_state(self.States.REWARD_UNAVAILABLE)

    def REWARD_UNAVAILABLE(self):
        if self.time_in_state() > self.lockout:
            self.change_state(self.States.REWARD_AVAILABLE)

    def is_complete(self):
        return self.time_elapsed() > self.duration * 60.0
