import random
from enum import Enum

from Components.BinaryInput import BinaryInput
from Events.InputEvent import InputEvent
from Tasks.Task import Task


class FearConditioning(Task):
    class States(Enum):
        INTER_TONE_INTERVAL = 0
        TONE = 1
        SHOCK = 2

    class Inputs(Enum):
        LEVER_PRESSED = 0
        LEVER_DEPRESSED = 1

    def __init__(self, *args):
        super().__init__(*args)
        self.cur_trial = 0
        self.reward_available = False
        self.prev_reward_time = 0
        self.reward_lockout = 0

    def start(self):
        self.cage_light.toggle(True)
        self.cur_trial = 0
        self.reward_available = True
        self.prev_reward_time = 0
        self.reward_lockout = 0
        self.state = self.States.INTER_TONE_INTERVAL
        super(FearConditioning, self).start()

    def main_loop(self):
        super().main_loop()
        if self.cur_time - self.prev_reward_time > self.reward_lockout:
            self.reward_available = True
        food_lever = self.food_lever.check()
        if food_lever == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.LEVER_PRESSED))
            if self.reward_available:
                self.food.dispense()
                self.reward_available = False
                self.reward_lockout = random.random() * self.max_reward_time
                self.prev_reward_time = self.cur_time
        elif food_lever == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.LEVER_DEPRESSED))
        if self.state == self.States.INTER_TONE_INTERVAL:
            if self.cur_trial < len(self.type_sequence) and self.time_elapsed() > self.time_sequence[2 * self.cur_trial]:
                self.change_state(self.States.TONE)
                self.tone.play_sound(self.tone_frequency, 1, self.time_sequence[2 * self.cur_trial + 1] - self.time_sequence[2 * self.cur_trial])
        elif self.state == self.States.TONE:
            if self.time_elapsed() > self.time_sequence[2 * self.cur_trial + 1]:
                if self.type_sequence[self.cur_trial] == 0:
                    self.change_state(self.States.INTER_TONE_INTERVAL)
                elif self.type_sequence[self.cur_trial] == 1:
                    self.change_state(self.States.SHOCK)
                    self.shocker.toggle(True)
                self.cur_trial += 1
        elif self.state == self.States.SHOCK:
            if self.time_in_state() > self.shock_duration:
                self.shocker.toggle(False)
                self.change_state(self.States.INTER_TONE_INTERVAL)

    def is_complete(self):
        return self.time_elapsed() > self.time_sequence[-1] + self.post_session_time

    def get_variables(self):
        return {
            'inter_tone_interval': 10,
            'tone_frequency': 1000,
            'time_sequence': [221, 251, 431, 461, 526, 556, 770, 800, 1020, 1050, 1257, 1287, 1467, 1497, 1636, 1666, 1848, 1876, 2139, 2169, 2240, 2270, 2490, 2520],
            'type_sequence': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
            'shock_duration': 0.5,
            'post_session_time': 30,
            'max_reward_time': 120
        }
