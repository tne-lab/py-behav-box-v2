import random
from enum import Enum

from Components.NosePoke import NosePoke
from Events.InputEvent import InputEvent

from Tasks.Task import Task


class SetShift(Task):
    class States(Enum):
        INITIATION = 0
        RESPONSE = 1
        INTER_TRIAL_INTERVAL = 2

    class Inputs(Enum):
        TROUGH_ENTERED = 0
        TROUGH_EXIT = 1
        FRONT_ENTERED = 2
        FRONT_EXIT = 3
        MIDDLE_ENTERED = 4
        MIDDLE_EXIT = 5
        REAR_ENTERED = 6
        REAR_EXIT = 7

    def __init__(self, chamber, source, address_file, protocol):
        super().__init__(chamber, source, address_file, protocol)
        self.cur_trial = 0
        self.cur_rule = 0
        self.cur_block = 0

    def start(self):
        self.cur_trial = 0
        self.cur_rule = 0
        self.cur_block = 0
        self.state = self.States.INITIATION
        self.nose_poke_lights[1].toggle(True)
        super(SetShift, self).start()

    def main_loop(self):
        super().main_loop()
        self.events = []
        pokes = []
        for i in range(3):
            pokes.append(self.nose_pokes[i].check())
            if pokes[i] == NosePoke.POKE_ENTERED:
                if i == 0:
                    self.events.append(InputEvent(self.Inputs.FRONT_ENTERED, self.cur_time - self.start_time))
                elif i == 1:
                    self.events.append(InputEvent(self.Inputs.MIDDLE_ENTERED, self.cur_time - self.start_time))
                elif i == 2:
                    self.events.append(InputEvent(self.Inputs.REAR_ENTERED, self.cur_time - self.start_time))
            elif pokes[i] == NosePoke.POKE_EXIT:
                if i == 0:
                    self.events.append(InputEvent(self.Inputs.FRONT_EXIT, self.cur_time - self.start_time))
                elif i == 1:
                    self.events.append(InputEvent(self.Inputs.MIDDLE_EXIT, self.cur_time - self.start_time))
                elif i == 2:
                    self.events.append(InputEvent(self.Inputs.REAR_EXIT, self.cur_time - self.start_time))
        trough_entered = self.food_trough.check()
        if trough_entered == NosePoke.POKE_ENTERED:
            self.events.append(InputEvent(self.Inputs.TROUGH_ENTERED, self.cur_time - self.start_time))
        elif trough_entered == NosePoke.POKE_EXIT:
            self.events.append(InputEvent(self.Inputs.TROUGH_EXIT, self.cur_time - self.start_time))
        if self.state == self.States.INITIATION:  # The rat has not initiated the trial yet
            if pokes[1] == NosePoke.POKE_ENTERED:
                self.nose_poke_lights[1].toggle(False)
                if self.light_sequence[self.cur_trial]:
                    self.nose_poke_lights[0].toggle(True)
                else:
                    self.nose_poke_lights[2].toggle(True)
                self.change_state(self.States.RESPONSE)
        elif self.state == self.States.RESPONSE:  # The rat has initiated a trial and must choose the correct option
            if pokes[0] == NosePoke.POKE_ENTERED or pokes[2] == NosePoke.POKE_ENTERED:
                if self.cur_trial < self.n_random_start or self.cur_trial >= self.n_random_start + self.correct_to_switch * len(
                        self.rule_sequence):
                    if random.random() < 0.5:
                        self.food.dispense()
                    self.cur_trial += 1
                else:
                    if self.rule_sequence[self.cur_rule] == 0:
                        if (pokes[0] == NosePoke.POKE_ENTERED and self.light_sequence[self.cur_trial]) or (
                                pokes[2] == NosePoke.POKE_ENTERED and not self.light_sequence[self.cur_trial]):
                            self.correct()
                        else:
                            self.cur_trial -= self.cur_block
                            self.cur_block = 0
                    elif self.rule_sequence[self.cur_rule] == 1:
                        if pokes[0] == NosePoke.POKE_ENTERED:
                            self.correct()
                        else:
                            self.cur_trial -= self.cur_block
                            self.cur_block = 0
                    elif self.rule_sequence[self.cur_rule] == 2:
                        if pokes[2] == NosePoke.POKE_ENTERED:
                            self.correct()
                        else:
                            self.cur_trial -= self.cur_block
                            self.cur_block = 0
                self.nose_poke_lights[0].toggle(False)
                self.nose_poke_lights[2].toggle(False)
                self.change_state(self.States.INTER_TRIAL_INTERVAL)
            elif self.cur_time - self.entry_time > self.response_duration:
                self.nose_poke_lights[0].toggle(False)
                self.nose_poke_lights[2].toggle(False)
                self.change_state(self.States.INTER_TRIAL_INTERVAL)
        elif self.state == self.States.INTER_TRIAL_INTERVAL:
            if self.cur_time - self.entry_time > self.inter_trial_interval:
                self.nose_poke_lights[1].toggle(True)
                self.change_state(self.States.INITIATION)
        return self.events

    def get_variables(self):
        return {
            'max_duration': 90,
            'inter_trial_interval': 7,
            'response_duration': 3,
            'n_random_start': 10,
            'n_random_end': 5,
            'rule_sequence': [0, 1, 0, 2, 0, 1, 0, 2],
            'correct_to_switch': 5,
            'light_sequence': random.sample([True for _ in range(27)] + [False for _ in range(28)], 55)
        }

    def is_complete(self):
        return self.cur_trial == self.n_random_start + self.n_random_end + self.correct_to_switch * len(
            self.rule_sequence) or self.cur_time - self.start_time > self.max_duration * 60

    def correct(self):
        self.food.dispense()
        if self.cur_block + 1 == self.correct_to_switch:
            self.cur_rule += 1
            self.cur_block = 0
        else:
            self.cur_block += 1
        self.cur_trial += 1
