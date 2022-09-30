from enum import Enum

from Tasks.Task import Task

from Components.BinaryInput import BinaryInput
from Components.TimedToggle import TimedToggle
from Components.Toggle import Toggle
from Events.InputEvent import InputEvent


class MiddleNosePokeTraining(Task):
    class States(Enum):
        ACTIVE = 0
        INTER_TRIAL_INTERVAL = 1

    class Inputs(Enum):
        MIDDLE_ENTERED = 0
        MIDDLE_EXIT = 1
        RESET_PRESSED = 2

    @staticmethod
    def get_components(self):
        return {
            'nose_pokes': [BinaryInput, BinaryInput, BinaryInput],
            'nose_poke_lights': [Toggle, Toggle, Toggle],
            'food': [TimedToggle],
            'house_light': [Toggle],
            'dispense_time': 0.7
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            "pokes": 0
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            'max_duration': 1.5,
            'pokes_to_complete': 20,
            'inter_trial_interval': 15
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

    def main_loop(self):
        middle_poke = self.nose_pokes[1].check()
        if middle_poke == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.MIDDLE_ENTERED))
        elif middle_poke == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.MIDDLE_EXIT))
        feed_press = self.feed_press.check()
        if feed_press == BinaryInput.ENTERED:
            self.pokes = 0
            self.events.append(InputEvent(self, self.Inputs.RESET_PRESSED))
        if self.state == self.States.ACTIVE:
            if middle_poke == BinaryInput.ENTERED:
                self.nose_poke_lights[1].toggle(False)
                self.food.toggle(self.dispense_time)
                self.pokes += 1
                self.change_state(self.States.INTER_TRIAL_INTERVAL)
        elif self.state == self.States.INTER_TRIAL_INTERVAL:
            if self.time_in_state() > self.inter_trial_interval:
                self.nose_poke_lights[1].toggle(True)
                self.change_state(self.States.ACTIVE)

    def is_complete(self):
        return self.time_elapsed() > self.max_duration * 60 * 60 or self.pokes == self.pokes_to_complete
