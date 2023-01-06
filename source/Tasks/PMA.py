import random
from enum import Enum

from Components.BinaryInput import BinaryInput
from Components.Toggle import Toggle
from Components.TimedToggle import TimedToggle
from Components.Video import Video
from Events.InputEvent import InputEvent
from Tasks.Task import Task

from Events.OEEvent import OEEvent


class PMA(Task):
    """@DynamicAttrs"""
    class States(Enum):
        INTER_TONE_INTERVAL = 0
        TONE = 1
        SHOCK = 2
        POST_SESSION = 3

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
            'shocker': [Toggle],
            'tone': [Toggle],
            'cam': [Video]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'ephys': False,
            'type': 'low',
            'random': True,
            'ntone': 20,
            'iti_min': 50,
            'iti_max': 150,
            'tone_duration': 30,
            'time_sequence': [96, 75, 79, 90, 80, 97, 88, 104, 77, 99, 102, 88, 101, 100, 96, 87, 78, 93, 89, 98],
            'shock_duration': 2,
            'post_session_time': 45,
            'dispense_time': 0.7
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            "cur_trial": 0,
            "reward_available": False,
            "presses": 0,
            "iti": self.iti_min + (self.iti_max - self.iti_min) * random.random()
        }

    def init_state(self):
        return self.States.INTER_TONE_INTERVAL

    def start(self):
        self.cage_light.toggle(True)
        self.cam.start()
        self.fan.toggle(True)
        if self.type == 'low':
            self.lever_out.toggle(True)
            self.food_light.toggle(True)

    def stop(self):
        if self.ephys:
            self.events.append([OEEvent(self, "stopRecord")])
        self.food_light.toggle(False)
        self.cage_light.toggle(False)
        self.fan.toggle(False)
        self.lever_out.toggle(False)
        self.shocker.toggle(False)
        self.tone.toggle(False)
        self.cam.stop()

    def handle_input(self) -> None:
        lever = self.food_lever.check()
        if lever == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.LEVER_PRESSED))
            self.food.toggle(self.dispense_time)
            self.presses += 1
        elif lever == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.LEVER_DEPRESSED))

    def INTER_TONE_INTERVAL(self):
        if (not self.random and self.cur_trial < len(self.time_sequence) and self.time_in_state() > self.time_sequence[
            self.cur_trial]) or (
                self.random and self.cur_trial < self.ntone and self.time_in_state() > self.iti):
            self.change_state(self.States.TONE)
            self.reward_available = True
            if not self.type == 'light':
                self.tone.toggle(True)
            if not self.type == 'low':
                self.lever_out.toggle(True)
                self.food_light.toggle(True)

    def TONE(self):
        if self.time_in_state() > self.tone_duration - self.shock_duration:
            self.change_state(self.States.SHOCK)
            if not self.type == 'light':
                self.shocker.toggle(True)
            self.cur_trial += 1
            self.iti = self.iti_min + (self.iti_max - self.iti_min) * random.random()

    def SHOCK(self):
        if self.time_in_state() > self.shock_duration:
            self.shocker.toggle(False)
            if (not self.random and self.cur_trial < len(self.time_sequence)) or (
                    self.random and self.cur_trial < self.ntone):
                self.change_state(self.States.INTER_TONE_INTERVAL)
            else:
                self.change_state(self.States.POST_SESSION)
            self.tone.toggle(False)
            if not self.type == 'low':
                self.lever_out.toggle(False)
                self.food_light.toggle(False)

    def is_complete(self):
        return self.cur_trial == len(self.time_sequence) and self.time_in_state() > self.post_session_time
