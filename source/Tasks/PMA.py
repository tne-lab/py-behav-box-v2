import time
from enum import Enum

from source.Components.BinaryInput import BinaryInput
from source.Events.InputEvent import InputEvent
from Tasks.Task import Task


class PMA(Task):
    class States(Enum):
        INTER_TONE_INTERVAL = 0
        TONE = 1
        SHOCK = 2
        POST_SESSION = 3

    class Inputs(Enum):
        LEVER_PRESSED = 0
        LEVER_DEPRESSED = 1

    def __init__(self, ws, chamber, source, address_file, protocol):
        super().__init__(ws, chamber, source, address_file, protocol)
        self.cur_trial = 0
        self.reward_available = False

    def start(self):
        self.cur_trial = 0
        self.state = self.States.INTER_TONE_INTERVAL
        self.cage_light.toggle(True)
        self.cam.start()
        self.fan.toggle(True)
        if self.type == 'low':
            self.lever_out.send(3)
            self.food_light.toggle(True)
        super(PMA, self).start()

    def stop(self):
        super(PMA, self).stop()
        self.food_light.toggle(False)
        self.cage_light.toggle(False)
        self.fan.toggle(False)
        self.lever_out.send(0)
        self.shocker.toggle(False)
        self.cam.stop()

    def main_loop(self):
        super().main_loop()
        food_lever = self.food_lever.check()
        if food_lever == BinaryInput.ENTERED:
            self.events.append(InputEvent(self.Inputs.LEVER_PRESSED, self.cur_time - self.start_time))
            self.food.dispense()
        elif food_lever == BinaryInput.EXIT:
            self.events.append(InputEvent(self.Inputs.LEVER_DEPRESSED, self.cur_time - self.start_time))
        if self.state == self.States.INTER_TONE_INTERVAL:
            if self.cur_trial < len(self.time_sequence) and self.cur_time - self.entry_time > self.time_sequence[self.cur_trial]:
                self.change_state(self.States.TONE)
                self.reward_available = True
                self.tone.toggle(True)
                if not self.type == 'low':
                    self.lever_out.send(3)
                    self.food_light.toggle(True)
        elif self.state == self.States.TONE:
            if self.cur_time - self.entry_time > self.tone_duration - self.shock_duration:
                self.change_state(self.States.SHOCK)
                self.shocker.toggle(True)
                self.cur_trial += 1
        elif self.state == self.States.SHOCK:
            if self.cur_time - self.entry_time > self.shock_duration:
                self.shocker.toggle(False)
                if self.cur_trial < len(self.time_sequence):
                    self.change_state(self.States.INTER_TONE_INTERVAL)
                else:
                    self.change_state(self.States.POST_SESSION)
                self.tone.toggle(False)
                if not self.type == 'low':
                    self.lever_out.send(0)
                    self.food_light.toggle(False)

    def is_complete(self):
        return self.cur_trial == len(self.time_sequence) and self.cur_time - self.entry_time > self.post_session_time

    def get_variables(self):
        return {
            'type': 'low',
            'inter_tone_interval': 10,
            'tone_duration': 30,
            'time_sequence': [10],
            'shock_duration': 2,
            'post_session_time': 45,
        }
