import random
from enum import Enum

from Components.Video import Video
from Components.TouchBinaryInput import TouchBinaryInput
from Components.BinaryInput import BinaryInput
from Components.Toggle import Toggle
from Components.TimedToggle import TimedToggle
from Events.InputEvent import InputEvent

from Tasks.Task import Task


class Bandit(Task):
    """@DynamicAttrs"""
    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2

    class Inputs(Enum):
        FOOD_ENTERED = 0
        FOOD_EXIT = 1
        FRONT_ENTERED = 2
        FRONT_EXIT = 3
        MIDDLE_ENTERED = 4
        MIDDLE_EXIT = 5
        REAR_ENTERED = 6
        REAR_EXIT = 7

    @staticmethod
    def get_components():
        return {
            'lights': [Toggle,Toggle, Toggle],
            'touches': [BinaryInput, BinaryInput, BinaryInput],
            'food_entry': [BinaryInput],
            'food': [TimedToggle],
            'food_light': [Toggle],
            'cam': [Video]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'max_duration': 180,
            'inter_trial_interval': 7,
            'response_duration': 3,
            'start_probs': [0.8, 0.1, 0.3],
            'history': 30,
            'accuracy': 0.7,
            'max_pellets': 150,
            'dispense_time': 0.7
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            'cur_probs': self.start_probs,
            'acc_seq': [0]*self.history,
            'n_reversal': 0
        }

    def init_state(self):
        return self.States.INITIATION

    def start(self):
        self.food_light.toggle(True)

    def stop(self):
        for light in self.lights:
            light.toggle(False)
        self.food_light.toggle(False)

    def main_loop(self):
        pokes = []
        for i in range(3):
            pokes.append(self.touches[i].check())
            if pokes[i] == BinaryInput.ENTERED:
                if i == 0:
                    self.events.append(InputEvent(self, self.Inputs.FRONT_ENTERED))
                elif i == 1:
                    self.events.append(InputEvent(self, self.Inputs.MIDDLE_ENTERED))
                elif i == 2:
                    self.events.append(InputEvent(self, self.Inputs.REAR_ENTERED))
            elif pokes[i] == BinaryInput.EXIT:
                if i == 0:
                    self.events.append(InputEvent(self, self.Inputs.FRONT_EXIT))
                elif i == 1:
                    self.events.append(InputEvent(self, self.Inputs.MIDDLE_EXIT))
                elif i == 2:
                    self.events.append(InputEvent(self, self.Inputs.REAR_EXIT))
        trough = self.food_entry.check()
        if trough == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.FOOD_ENTERED))
        elif trough == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.FOOD_EXIT))
        if self.state == self.States.INITIATION:  # The rat has not initiated the trial yet
            if trough == BinaryInput.ENTERED:
                for light in self.lights:
                    light.toggle(True)
                self.food_light.toggle(False)
                self.change_state(self.States.RESPONSE)
        elif self.state == self.States.RESPONSE:  # The rat has initiated a trial and must choose the correct option
            metadata = {}
            if pokes[0] == BinaryInput.ENTERED or pokes[1] == BinaryInput.ENTERED or pokes[2] == BinaryInput.ENTERED:
                if pokes[0] == BinaryInput.ENTERED:
                    loc = 0
                elif pokes[1] == BinaryInput.ENTERED:
                    loc = 1
                else:
                    loc = 2
                if random.random() < self.cur_probs[loc]:
                    self.food.toggle(self.dispense_time)
                    metadata["rewarded"] = "True"
                else:
                    metadata["rewarded"] = "False"
                metadata["rule_index"] = -1
                self.acc_seq.pop()
                if self.cur_probs[loc] == 0.8:
                    metadata["accuracy"] = "True"
                    self.acc_seq.insert(0, 1)
                else:
                    metadata["accuracy"] = "False"
                    self.acc_seq.insert(0, 0)
                if sum(self.acc_seq) >= self.history*self.accuracy:
                    self.n_reversal += 1
                    swap = random.sample(range(3), 2)
                    temp = self.cur_probs[swap[0]]
                    self.cur_probs[swap[0]] = self.cur_probs[swap[1]]
                    self.cur_probs[swap[1]] = temp
                    metadata["reversal"] = self.cur_probs
                    self.acc_seq = [0]*self.history
                for light in self.lights:
                    light.toggle(False)
                self.change_state(self.States.INTER_TRIAL_INTERVAL, metadata)
            elif self.time_in_state() > self.response_duration:
                metadata["accuracy"] = "none"
                metadata["rewarded"] = "none"
                for light in self.lights:
                    light.toggle(False)
                self.change_state(self.States.INTER_TRIAL_INTERVAL, metadata)
        elif self.state == self.States.INTER_TRIAL_INTERVAL:
            if self.time_in_state() > self.inter_trial_interval:
                self.food_light.toggle(True)
                self.change_state(self.States.INITIATION)

    def is_complete(self):
        return self.food.count == self.max_pellets or self.time_elapsed() > self.max_duration*60
