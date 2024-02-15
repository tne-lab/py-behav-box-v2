from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pybehave.Sources.Source import Source

import math
import numpy as np
from pybehave.Components.Stimmer import Stimmer
from pybehave.Components.Component import Component


class WaveformStim(Stimmer):

    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.state = False
        self.configs = {}
        self.sr = None

    def parametrize(self, pnum: int, _, per: int, dur: int, amps: np.ndarray, durs: list[int]) -> None:
        waveforms = np.zeros((amps.shape[0], math.ceil(dur/1000000*self.sr) + 1))
        ns = 0
        while ns < math.ceil(dur/1000000*self.sr):
            sw = 0
            for i in range(amps.shape[1]):
                for j in range(math.floor(durs[i] / 1000000 * self.sr)):
                    for k in range(amps.shape[0]):
                        waveforms[k, ns] = amps[k, i]
                    ns += 1
                sw += math.floor(durs[i] / 1000000 * self.sr)
            ns += math.ceil(per / 1000000 * self.sr) - sw
        for i in range(amps.shape[0]):
            waveforms[i, -1] = 0
        self.configs[pnum] = waveforms

    def start(self, pnum: int, stype: str = None) -> None:
        self.state = True  # Ideally make this false when stim is done
        self.write(self.configs[pnum])

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.ANALOG_OUTPUT
