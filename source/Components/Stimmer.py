from __future__ import annotations
from typing import TYPE_CHECKING

from Components.Output import Output

if TYPE_CHECKING:
    import numpy as np

from abc import ABCMeta, abstractmethod
from Components.Component import Component


class Stimmer(Output):
    __metaclass__ = ABCMeta

    @abstractmethod
    def parametrize(self, pnum: int, outs: list[int], per: int, dur: int, amps: np.ndarray, durs: list[int]) -> None:
        #raise NotImplementedError
        pass

    @abstractmethod
    def start(self, pnum: int, stype: str) -> None:
        #raise NotImplementedError
        pass

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.OUTPUT
