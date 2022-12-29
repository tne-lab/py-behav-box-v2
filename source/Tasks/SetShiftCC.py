from Components.Input import Input
from Components.Output import Output
from Components.BinaryInput import BinaryInput
from Components.Stimmer import Stimmer
from Tasks.SetShift import SetShift


class SetShiftCC(SetShift):
    
    @staticmethod
    def get_components():
        comps = super(SetShiftCC, SetShiftCC).get_components()
        comps['bayes_read'] = [Input]
        comps['bayes_write'] = [Output]
        comps['stim'] = [Stimmer]
        return comps

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        constants = super(SetShiftCC, self).get_constants()
        constants['fit'] = False
        return constants

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        variables = super(SetShiftCC, self).get_variables()
        variables['params'] = None
        return variables

    def stop(self):
        super(SetShiftCC, self).stop()
        self.bayes_write.set({'command': 'Save'})

    def handle_input(self):
        super(SetShiftCC, self).handle_input()
        new_params = self.bayes_read.check()
        if self.params != new_params:
            self.params = new_params
            # Do Stim

    def RESPONSE(self):
        if self.pokes[0] == BinaryInput.ENTERED or self.pokes[2] == BinaryInput.ENTERED:
            if self.fit:
                self.bayes_write.set({'command': 'NewDataFit', 'outcome': self.time_in_state(), 'params': self.params})
            else:
                self.bayes_write.set({'command': 'NewData', 'outcome': self.time_in_state(), 'params': self.params})
                # Generate new random params
        elif self.time_in_state() > self.response_duration:
            self.bayes_write.set({'command': 'Suggest'})

        super(SetShiftCC, self).RESPONSE()
