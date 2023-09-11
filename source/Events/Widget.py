from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget

if TYPE_CHECKING:
    from Workstation.ChamberWidget import ChamberWidget


class Widget:
    __metaclass__ = ABCMeta

    def __init__(self, name: str):
        self.name = name
        self.cw = None

    def set_chamber(self, cw: ChamberWidget):
        self.cw = cw

    @abstractmethod
    def get_widget(self) -> QWidget:
        raise NotImplementedError

    def close_(self):
        self.close()

    def close(self):
        pass

