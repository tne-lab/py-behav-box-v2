import math

import numpy as np
from Components.Stimmer import Stimmer
from Components.Component import Component


class WaveformStim(Stimmer):

    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def parametrize(self, pnum, _, per, dur, amps, durs):
        waveforms = np.zeros(amps.shape[0], math.ceil(dur/1000000*self.sr) + 1)
        ns = 0
        while ns < math.ceil(dur/1000000*self.sr):
            sw = 0
            for i in range(amps.shape[1]):
                for j in range(durs[i] / 1000000 * self.sr):
                    for k in range(amps.shape[0]):
                        waveforms[k, ns] = amps[k, i]
                    ns += 1
                sw += durs[i] / 1000000 * self.sr
            ns += per - sw
        for i in range(amps.shape[0]):
            waveforms[i, -1] = 0
        self.configs[pnum] = waveforms

    def start(self, pnum, _):
        self.state = True  # Ideally make this false when stim is done
        self.source.write_component(self.configs[pnum])

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.ANALOG_OUTPUT
