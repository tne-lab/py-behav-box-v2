import random
from enum import Enum

from Components.BinaryInput import BinaryInput
from Components.Toggle import Toggle
from Components.TimedToggle import TimedToggle
from Events.InputEvent import InputEvent

from Tasks.Task import Task


class SetShift(Task):
    """@DynamicAttrs"""
    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2

    class Inputs(Enum):
        FRONT_ENTERED = 2
        FRONT_EXIT = 3
        MIDDLE_ENTERED = 4
        MIDDLE_EXIT = 5
        REAR_ENTERED = 6
        REAR_EXIT = 7

    @staticmethod
    def get_components():
        return {
            'nose_pokes': [BinaryInput, BinaryInput, BinaryInput],
            'nose_poke_lights': [Toggle, Toggle, Toggle],
            'food': [TimedToggle],
            'house_light': [Toggle, Toggle]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'max_duration': 90,
            'inter_trial_interval': 7,
            'response_duration': 3,
            'n_random_start': 10,
            'n_random_end': 5,
            'rule_sequence': [0, 1, 0, 2, 0, 1, 0, 2],
            'correct_to_switch': 5,
            'light_sequence': random.sample([True for _ in range(27)] + [False for _ in range(28)], 55),
            'dispense_time': 0.7
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            'cur_trial': 0,
            'cur_rule': 0,
            'cur_block': 0,
            'pokes': []
        }

    def init_state(self):
        return self.States.INITIATION

    def start(self):
        self.nose_poke_lights[1].toggle(True)
        self.house_light[0].toggle(True)
        self.house_light[1].toggle(True)

    def stop(self):
        for i in range(3):
            self.nose_poke_lights[i].toggle(False)
        self.house_light[0].toggle(False)
        self.house_light[1].toggle(False)

    def handle_input(self):
        self.pokes = []
        for i in range(3):
            self.pokes.append(self.nose_pokes[i].check())
            if self.pokes[i] == BinaryInput.ENTERED:
                if i == 0:
                    self.events.append(InputEvent(self, self.Inputs.FRONT_ENTERED))
                elif i == 1:
                    self.events.append(InputEvent(self, self.Inputs.MIDDLE_ENTERED))
                elif i == 2:
                    self.events.append(InputEvent(self, self.Inputs.REAR_ENTERED))
            elif self.pokes[i] == BinaryInput.EXIT:
                if i == 0:
                    self.events.append(InputEvent(self, self.Inputs.FRONT_EXIT))
                elif i == 1:
                    self.events.append(InputEvent(self, self.Inputs.MIDDLE_EXIT))
                elif i == 2:
                    self.events.append(InputEvent(self, self.Inputs.REAR_EXIT))

    def INITIATION(self):
        if self.pokes[1] == BinaryInput.ENTERED:
            self.nose_poke_lights[1].toggle(False)
            if self.light_sequence[self.cur_trial]:
                self.nose_poke_lights[0].toggle(True)
            else:
                self.nose_poke_lights[2].toggle(True)
            self.change_state(self.States.RESPONSE, {"light_location": self.light_sequence[self.cur_trial]})

    def RESPONSE(self):
        metadata = {}
        if self.pokes[0] == BinaryInput.ENTERED or self.pokes[2] == BinaryInput.ENTERED:
            if self.cur_trial < self.n_random_start or self.cur_trial >= self.n_random_start + self.correct_to_switch * len(
                    self.rule_sequence):
                if random.random() < 0.5:
                    self.food.toggle(self.dispense_time)
                    metadata["accuracy"] = "correct"
                else:
                    metadata["accuracy"] = "incorrect"
                self.cur_trial += 1
                metadata["rule_index"] = -1
            else:
                metadata["rule"] = self.rule_sequence[self.cur_rule]
                metadata["cur_block"] = self.cur_block
                metadata["rule_index"] = self.cur_rule
                if self.rule_sequence[self.cur_rule] == 0:
                    if (self.pokes[0] == BinaryInput.ENTERED and self.light_sequence[self.cur_trial]) or (
                            self.pokes[2] == BinaryInput.ENTERED and not self.light_sequence[self.cur_trial]):
                        self.correct()
                        metadata["accuracy"] = "correct"
                    else:
                        self.cur_trial -= self.cur_block
                        self.cur_block = 0
                        metadata["accuracy"] = "incorrect"
                elif self.rule_sequence[self.cur_rule] == 1:
                    if self.pokes[0] == BinaryInput.ENTERED:
                        self.correct()
                        metadata["accuracy"] = "correct"
                    else:
                        self.cur_trial -= self.cur_block
                        self.cur_block = 0
                        metadata["accuracy"] = "incorrect"
                elif self.rule_sequence[self.cur_rule] == 2:
                    if self.pokes[2] == BinaryInput.ENTERED:
                        self.correct()
                        metadata["accuracy"] = "correct"
                    else:
                        self.cur_trial -= self.cur_block
                        self.cur_block = 0
                        metadata["accuracy"] = "incorrect"
            self.nose_poke_lights[0].toggle(False)
            self.nose_poke_lights[2].toggle(False)
            self.change_state(self.States.INTER_TRIAL_INTERVAL, metadata)
        elif self.time_in_state() > self.response_duration:
            metadata["rule"] = self.rule_sequence[self.cur_rule]
            metadata["cur_block"] = self.cur_block
            metadata["rule_index"] = self.cur_rule
            metadata["accuracy"] = "incorrect"
            metadata["response"] = "none"
            self.nose_poke_lights[0].toggle(False)
            self.nose_poke_lights[2].toggle(False)
            self.change_state(self.States.INTER_TRIAL_INTERVAL, metadata)

    def INTER_TRIAL_INTERVAL(self):
        if self.time_in_state() > self.inter_trial_interval:
            self.nose_poke_lights[1].toggle(True)
            self.change_state(self.States.INITIATION)

    def is_complete(self):
        return self.cur_trial == self.n_random_start + self.n_random_end + self.correct_to_switch * len(
            self.rule_sequence) or self.time_elapsed() > self.max_duration * 60

    def correct(self):
        self.food.toggle(self.dispense_time)
        if self.cur_block + 1 == self.correct_to_switch:
            self.cur_rule += 1
            self.cur_block = 0
        else:
            self.cur_block += 1
        self.cur_trial += 1
