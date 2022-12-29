from enum import Enum
from random import randint
import numpy as np

from Tasks.Task import Task
from Components.BinaryInput import BinaryInput
from Components.Video import Video
from Components.ParametricStim import ParametricStim
from Events.InputEvent import InputEvent


class OptoControl(Task):
    """@DynamicAttrs"""
    class States(Enum):
        IN_TRIAL = 0
        DELAY = 1

    class Inputs(Enum):
        LIGHT_ON = 0
        LIGHT_OFF = 1

    @staticmethod
    def get_components():
        return {
            'front_light': [BinaryInput],
            'rear_light': [BinaryInput],
            'stim': [ParametricStim],
            'cam': [Video]
        }

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        return {
            'delay': 3.5,
            'periods': [7692],
            'pws': [1000, 5000],
            'amps_0': [1000, 2000, 3000],
            'amps_1': [0, 0, 0],
            'vid_enabled': True,
            'block_len': 1,
            'mode_0': 0,
            'mode_1': 3,
            'biphasic': False
        }

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        return {
            'pw': 0,
            'amp': 0,
            'per': self.periods[0],
            'counts': np.zeros((len(self.pws), len(self.amps_0), len(self.periods))),
            'complete': False,
            'nstim': 0,
            'noff': 0,
            'trial_in_block': 0,
            'stim_change': False
        }

    def init_state(self):
        return self.States.IN_TRIAL

    def init(self):
        self.stim.parametrize(0, [3, 3], 7692, 7692, np.reshape(np.array([0, 0]), (2, 1)), np.array([1000]))
        stim_id = 1
        for i in range(self.counts.shape[0]):
            for j in range(self.counts.shape[1]):
                for k in range(self.counts.shape[2]):
                    if self.biphasic:
                        self.stim.parametrize(stim_id, [self.mode_0, self.mode_1], self.periods[k], 100000000000,
                                              np.array([[self.amps_0[j], -self.amps_0[j]], [self.amps_1[j], -self.amps_1[j]]]),
                                              np.array([self.pws[i], self.pws[i]]))
                    else:
                        self.stim.parametrize(stim_id, [self.mode_0, self.mode_1], self.periods[k], 100000000000,
                                              np.reshape(np.array([self.amps_0[j], self.amps_1[j]]), (2, 1)), np.array([self.pws[i]]))
                    stim_id += 1

    def start(self):
        self.stim.start(0)
        if self.vid_enabled:
            self.cam.start()

    def stop(self):
        self.stim.start(0)
        if self.vid_enabled:
            self.cam.stop()

    def handle_input(self) -> None:
        front_active = self.front_light.check()
        rear_active = self.rear_light.check()
        self.stim_change = False
        if front_active == BinaryInput.ENTERED or rear_active == BinaryInput.ENTERED:
            self.events.append(InputEvent(self, self.Inputs.LIGHT_ON))
        elif front_active == BinaryInput.EXIT or rear_active == BinaryInput.EXIT:
            self.events.append(InputEvent(self, self.Inputs.LIGHT_OFF))
            self.stim_change = True

    def IN_TRIAL(self):
        if self.stim_change:
            self.change_state(self.States.DELAY)

    def DELAY(self):
        if self.time_in_state() > self.delay:
            self.trial_in_block += 1
            if self.trial_in_block == self.block_len:
                if self.pw == 0:
                    min_count = np.amin(self.counts)
                    valid_params = np.where(self.counts == min_count)
                    test_ind = randint(0, len(valid_params[0])) - 1
                    self.counts[valid_params[0][test_ind], valid_params[1][test_ind], valid_params[2][test_ind]] += 1
                    self.pw = self.pws[valid_params[0][test_ind]]
                    self.amp = self.amps_0[valid_params[1][test_ind]]
                    self.per = self.periods[valid_params[2][test_ind]]
                    self.nstim += 1
                    self.stim.start(
                        len(self.amps_0) * valid_params[0][test_ind] + valid_params[1][test_ind] + valid_params[2][
                            test_ind] + 1)
                else:
                    self.pw = 0
                    self.amp = 0
                    self.noff += 1
                    self.stim.start(0)
                self.trial_in_block = 0
                self.change_state(self.States.IN_TRIAL, {"pw": self.pw, "amp": self.amp, "per": self.per})
            else:
                self.change_state(self.States.IN_TRIAL, None)

    def is_complete(self):
        return self.complete

