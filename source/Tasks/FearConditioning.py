import random
from enum import Enum

from Components.BinaryInput import BinaryInput
from Components.Toggle import Toggle
from Components.TimedToggle import TimedToggle
from Events.InputEvent import InputEvent
from Tasks.Task import Task


class FearConditioning(Task):
    """@DynamicAttrs"""
    class States(Enum):
        INTER_TONE_INTERVAL = 0
        TONE = 1
        SHOCK = 2

    class Inputs(Enum):
        LEVER_PRESSED = 0
        LEVER_DEPRESSED = 1

    @staticmethod
    def get_components():
        return {
            "food_lever": [BinaryInput],
            "cage_light": [Toggle],
            "food": [TimedToggle],
            "tone": [Toggle],
            "fan": [Toggle],
            "shocker": [Toggle]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'inter_tone_interval': 10,
            'tone_frequency': 1000,
            'time_sequence': [221, 251, 431, 461, 526, 556, 770, 800, 1020, 1050, 1257, 1287, 1467, 1497, 1636, 1666, 1848, 1876, 2139, 2169, 2240, 2270, 2490, 2520],
            'type_sequence': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
            'shock_duration': 0.5,
            'post_session_time': 30,
            'max_reward_time': 120,
            'dispense_time': 0.7
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            "cur_trial": 0,
            "reward_available": False,
            "prev_reward_time": 0,
            "reward_lockout": 0
        }

    def init_state(self):
        return self.States.INTER_TONE_INTERVAL

    def start(self):
        self.cage_light.toggle(True)

    def handle_input(self) -> None:
        if self.cur_time - self.prev_reward_time > self.reward_lockout:
            self.reward_available = True
        food_lever = self.food_lever.check()
        if food_lever == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.LEVER_PRESSED))
            if self.reward_available:
                self.food.toggle(self.dispense_time)
                self.reward_available = False
                self.reward_lockout = random.random() * self.max_reward_time
                self.prev_reward_time = self.cur_time
        elif food_lever == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.LEVER_DEPRESSED))

    def INTER_TONE_INTERVAL(self):
        if self.cur_trial < len(self.type_sequence) and self.time_elapsed() > self.time_sequence[2 * self.cur_trial]:
            self.change_state(self.States.TONE)
            self.tone.play_sound(self.tone_frequency, 1,
                                 self.time_sequence[2 * self.cur_trial + 1] - self.time_sequence[2 * self.cur_trial])

    def TONE(self):
        if self.time_elapsed() > self.time_sequence[2 * self.cur_trial + 1]:
            if self.type_sequence[self.cur_trial] == 0:
                self.change_state(self.States.INTER_TONE_INTERVAL)
            elif self.type_sequence[self.cur_trial] == 1:
                self.change_state(self.States.SHOCK)
                self.shocker.toggle(True)
            self.cur_trial += 1

    def SHOCK(self):
        if self.time_in_state() > self.shock_duration:
            self.shocker.toggle(False)
            self.change_state(self.States.INTER_TONE_INTERVAL)

    def is_complete(self):
        return self.time_elapsed() > self.time_sequence[-1] + self.post_session_time
