from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source
    import numpy as np

from Components.Stimmer import Stimmer


class ParametricStim(Stimmer):

    def __init__(self, source: Source, component_id: str, component_address: str):
        self.state = False
        super().__init__(source, component_id, component_address)

    def trigger(self, ichan: int, pnum: int, falling: int = 0) -> None:
        self.source.write_component(self.id, "R{},{},{}".format(ichan, pnum, falling))

    def parametrize(self, pnum: int, outs: list[int], per: int, dur: int, amps: np.ndarray, durs: list[int]) -> None:
        stimulus = "S{},{},{},{},{}".format(pnum, outs[0], outs[1], per, dur)
        for i in range(amps.shape[1]):
            stimulus += "; "
            for j in range(amps.shape[0]):
                stimulus += "{},".format(amps[j, i])
            stimulus += "{}".format(durs[i])
        self.source.write_component(self.id, stimulus)

    def start(self, pnum: int, stype: str = "T") -> None:
        self.state = True
        self.source.write_component(self.id, "{}{}".format(stype, pnum))

    def update_parameters(self, per: int, amps: np.ndarray, durs: list[int]) -> None:
        stimulus = "F{}".format(per)
        for i in range(amps.shape[1]):
            stimulus += "; "
            for j in range(amps.shape[0]):
                stimulus += "{},".format(amps[j, i])
            stimulus += "{}".format(durs[i])
        self.source.write_component(self.id, stimulus)
