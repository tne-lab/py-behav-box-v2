from __future__ import annotations
from abc import ABCMeta
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QWidget

if TYPE_CHECKING:
    from pybehave.Workstation.ChamberWidget import ChamberWidget


class Widget(QWidget):
    __metaclass__ = ABCMeta

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.cw = None

    def set_chamber(self, cw: ChamberWidget):
        self.cw = cw

    def close_(self):
        self.close()

    def close(self):
        pass

