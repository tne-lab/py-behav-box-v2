from collections import OrderedDict

import numpy as np

from Components.Input import Input
from Components.Output import Output
from Components.BinaryInput import BinaryInput
from Components.Stimmer import Stimmer
from Events.InputEvent import InputEvent
from Tasks.SetShift import SetShift


class SetShiftCL(SetShift):
    class Inputs(SetShift.Inputs):
        STIM_CHANGE = 8

    @staticmethod
    def get_components():
        comps = super(SetShiftCL, SetShiftCL).get_components()
        comps['bayes_read'] = [Input]
        comps['bayes_write'] = [Output]
        comps['stim'] = [Stimmer]
        return comps

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        constants = super(SetShiftCL, self).get_constants()
        constants['fit'] = False
        constants['delay'] = 3.5
        return constants

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        variables = super(SetShiftCL, self).get_variables()
        variables['params'] = OrderedDict([('period', 7692), ('amp', 0), ('pw', 100)])
        return variables

    def start(self):
        super(SetShiftCL, self).start()
        self.stim.parametrize(0, [0, 0], self.params['period'], 100000000000,
                              self.params['amp'] * np.array([[1, -1], [1, -1]]), self.params['pw'] * np.array([1, 1]))
        self.stim.start(0)

    def stop(self):
        super(SetShiftCL, self).stop()
        self.bayes_write.set({'command': 'Save'})
        self.stim.parametrize(0, [3, 3], 1000, self.params['period'], np.array([[0], [0]]), np.array([100]))
        self.stim.start(0)

    def handle_input(self):
        super(SetShiftCL, self).handle_input()
        new_params = self.bayes_read.check()
        if self.state == self.States.INTER_TRIAL_INTERVAL and self.time_in_state() > self.delay and self.params != new_params:
            self.params = new_params
            self.stim.update_parameters(self.params['period'], self.params['amp'] * np.array([[1, -1], [1, -1]]),
                                        self.params['pw'] * np.array([1, 1]))
            self.events.append(InputEvent(self, self.Inputs.STIM_CHANGE, self.params))

    def RESPONSE(self):
        if self.pokes[0] == BinaryInput.ENTERED or self.pokes[2] == BinaryInput.ENTERED:
            if self.fit:
                self.bayes_write.set({'command': 'NewDataFit', 'outcome': self.time_in_state(), 'params': self.params})
            else:
                self.bayes_write.set({'command': 'NewData', 'outcome': self.time_in_state(), 'params': self.params})
                self.bayes_write.set({'command': 'Suggest'})
        elif self.time_in_state() > self.response_duration:
            self.bayes_write.set({'command': 'Suggest'})
        super(SetShiftCL, self).RESPONSE()
