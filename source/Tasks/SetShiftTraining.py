import random
from enum import Enum

from Tasks.Task import Task

from Components.BinaryInput import BinaryInput
from Components.TimedToggle import TimedToggle
from Components.Toggle import Toggle
from Events.InputEvent import InputEvent


class MiddleNosePokeTraining(Task):
    """@DynamicAttrs"""
    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2

    class Inputs(Enum):
        MIDDLE_ENTERED = 0
        MIDDLE_EXIT = 1
        FRONT_ENTERED = 2
        FRONT_EXIT = 3
        REAR_ENTERED = 4
        REAR_EXIT = 5
        RESET_PRESSED = 6

    @staticmethod
    def get_components():
        return {
            'nose_pokes': [BinaryInput, BinaryInput, BinaryInput],
            'nose_poke_lights': [Toggle, Toggle, Toggle],
            'food': [TimedToggle],
            'house_light': [Toggle]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            "pokes": 0,
            'dispense_time': 0.7,
            'training_stage': 'middle',

        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            'max_duration': 1.5,
            'pokes_to_complete': 20,
            'inter_trial_interval': 15,
            'poke_vec': []
        }

    def init_state(self):
        return self.States.INTER_TRIAL_INTERVAL

    def start(self):
        self.house_light.toggle(True)
        self.house_light2.toggle(True)

    def stop(self):
        self.house_light.toggle(False)
        self.house_light2.toggle(False)
        self.nose_poke_lights[1].toggle(False)

    def handle_input(self) -> None:
        self.poke_vec = []
        for i in range(3):
            self.poke_vec.append(self.nose_pokes[i].check())
            if self.poke_vec[i] == BinaryInput.ENTERED:
                if i == 0:
                    self.events.append(InputEvent(self, self.Inputs.FRONT_ENTERED))
                elif i == 1:
                    self.events.append(InputEvent(self, self.Inputs.MIDDLE_ENTERED))
                elif i == 2:
                    self.events.append(InputEvent(self, self.Inputs.REAR_ENTERED))
            elif self.poke_vec[i] == BinaryInput.EXIT:
                if i == 0:
                    self.events.append(InputEvent(self, self.Inputs.FRONT_EXIT))
                elif i == 1:
                    self.events.append(InputEvent(self, self.Inputs.MIDDLE_EXIT))
                elif i == 2:
                    self.events.append(InputEvent(self, self.Inputs.REAR_EXIT))
        feed_press = self.feed_press.check()
        if feed_press == BinaryInput.ENTERED:
            self.pokes = 0
            self.events.append(InputEvent(self, self.Inputs.RESET_PRESSED))

    def RESPONSE(self):
        if self.poke_vec[0] == BinaryInput.ENTERED or self.poke_vec[2] == BinaryInput.ENTERED:
            if self.poke_vec[0] == BinaryInput.ENTERED:
                if (self.nose_pokes[
                        0].get_state() and self.training_stage == 'light') or self.training_stage == 'front':
                    self.food.toggle(self.dispense_time)
                    self.pokes += 1
                    self.nose_pokes[0].toggle(False)
                    self.nose_pokes[2].toggle(False)
                    self.change_state(self.States.INTER_TRIAL_INTERVAL)
            elif self.poke_vec[2] == BinaryInput.ENTERED:
                if (self.nose_pokes[2].get_state() and self.training_stage == 'light') or self.training_stage == 'rear':
                    self.food.toggle(self.dispense_time)
                    self.pokes += 1
                    self.nose_pokes[0].toggle(False)
                    self.nose_pokes[2].toggle(False)
                    self.change_state(self.States.INTER_TRIAL_INTERVAL)

    def INITIATION(self):
        if self.poke_vec[1] == BinaryInput.ENTERED:
            self.nose_poke_lights[1].toggle(False)
            if self.training_stage == 'middle':
                self.food.toggle(self.dispense_time)
                self.pokes += 1
                self.change_state(self.States.INTER_TRIAL_INTERVAL)
            else:
                self.nose_pokes[2 * random.randint(0, 1)].toggle(True)
                self.change_state(self.States.RESPONSE)

    def INTER_TRIAL_INTERVAL(self):
        if self.time_in_state() > self.inter_trial_interval:
            self.nose_poke_lights[1].toggle(True)
            self.change_state(self.States.INITIATION)

    def is_complete(self):
        return self.time_elapsed() > self.max_duration * 60 * 60 or self.pokes == self.pokes_to_complete
