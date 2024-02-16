from __future__ import annotations
from typing import TYPE_CHECKING

from pybehave.Components.Output import Output

if TYPE_CHECKING:
    import numpy as np

from pybehave.Components.Component import Component


class Stimmer(Output):

    def parametrize(self, pnum: int, outs: list[int], per: int, dur: int, amps: np.ndarray, durs: list[int]) -> None:
        pass

    def start(self, pnum: int, stype: str = None) -> None:
        pass

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.OUTPUT
