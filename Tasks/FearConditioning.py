import random

from Components.Lever import Lever
from Tasks.Task import Task


class FearConditioning(Task):
    class States(Enum):
        INTER_TONE_INTERVAL = 0
        TONE_NO_SHOCK = 1
        TONE_SHOCK = 2

    class Inputs(Enum):
        LEVER_PRESSED = 0
        LEVER_DEPRESSED = 1

    def __init__(self, ws, source, address_file, protocol):
        super().__init__(ws, source, address_file, protocol)
        for i in range(len(self.coords)):
            self.coords[i] = (self.coords[i][0], self.coords[i][1] + self.dead_height)
        self.cur_trial = 0
        self.state = self.States.INTER_TONE_INTERVAL

    def main_loop(self):
        super().main_loop()
        self.events = []
        food_lever = self.food_lever.check()
        if food_lever == Lever.LEVER_PRESSED:
            self.events.append(InputEvent(self.Inputs.LEVER_PRESSED, self.cur_time - self.start_time))
            self.food.dispense()
        elif init_poke == Lever.LEVER_DEPRESSED:
            self.events.append(InputEvent(self.Inputs.LEVER_DEPRESSED, self.cur_time - self.start_time))
        if self.state == self.States.INTER_TONE_INTERVAL:
            if self.cur_time - self.entry_time > self.inter_tone_interval:
                if random.random() < 0.5:
                    self.change_state(self.States.TONE_NO_SHOCK)
                    self.tone.play_sound(self.tone_frequency, self.tone_duration, 1)
                else:
                    self.change_state(self.States.TONE_SHOCK)
                    self.tone.play_sound(self.tone_frequency, self.tone_duration, 1)
                    self.shocker.toggle(True)
        elif self.state == self.States.TONE_NO_SHOCK:
            if self.cur_time - self.entry_time > self.tone_duration:
                self.change_state(self.States.INTER_TONE_INTERVAL)
        elif self.state == self.States.TONE_SHOCK:
            if self.cur_time - self.entry_time > self.tone_duration:
                self.shocker.toggle(False)
                self.change_state(self.States.INTER_TONE_INTERVAL)

    def get_variables(self):
        return {
            'n_tones': 20,
            'inter_tone_interval': 10,
            'tone_frequency': 1000,
            'tone_duration': 10
        }
