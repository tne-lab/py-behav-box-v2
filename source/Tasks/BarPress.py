from enum import Enum

import random
from Components.BinaryInput import BinaryInput
from Events.InputEvent import InputEvent
from Tasks.Task import Task


class BarPress(Task):
    class States(Enum):
        REWARD_AVAILABLE = 0
        REWARD_UNAVAILABLE = 1

    class Inputs(Enum):
        LEVER_PRESSED = 0
        LEVER_DEPRESSED = 1

    def __init__(self, ws, chamber, source, address_file, protocol):
        super().__init__(ws, chamber, source, address_file, protocol)
        self.presses = 0
        self.lockout = 0

    def start(self):
        self.state = self.States.REWARD_AVAILABLE
        self.cage_light.toggle(True)
        self.cam.start()
        self.fan.toggle(True)
        self.presses = 0
        self.lever_out.send(3)
        self.food_light.toggle(True)
        self.lockout = 0
        super(BarPress, self).start()

    def stop(self):
        super(BarPress, self).stop()
        self.food_light.toggle(False)
        self.cage_light.toggle(False)
        self.fan.toggle(False)
        self.lever_out.send(0)
        self.cam.stop()

    def main_loop(self):
        super().main_loop()
        food_lever = self.food_lever.check()
        pressed = False
        if food_lever == BinaryInput.ENTERED:
            self.events.append(InputEvent(self.Inputs.LEVER_PRESSED, self.cur_time - self.start_time))
            pressed = True
            self.presses += 1
        elif food_lever == BinaryInput.EXIT:
            self.events.append(InputEvent(self.Inputs.LEVER_DEPRESSED, self.cur_time - self.start_time))
        if self.state == self.States.REWARD_AVAILABLE:
            if pressed:
                self.food.dispense()
                if self.reward_lockout:
                    self.lockout = self.reward_lockout_min+random.random()*(self.reward_lockout_max-self.reward_lockout_min)
                    self.change_state(self.States.REWARD_UNAVAILABLE)
        elif self.state == self.States.REWARD_UNAVAILABLE:
            if self.cur_time - self.entry_time > self.lockout:
                self.change_state(self.States.REWARD_AVAILABLE)

    def is_complete(self):
        return self.cur_time - self.start_time > self.duration * 60.0

    def get_variables(self):
        return {
            'duration': 40,
            'reward_lockout': False,
            'reward_lockout_min': 25,
            'reward_lockout_max': 35
        }
