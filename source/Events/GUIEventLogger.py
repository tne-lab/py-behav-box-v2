from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget
    from Workstation.ChamberWidget import ChamberWidget

from abc import ABCMeta, abstractmethod

from Events.EventLogger import EventLogger


class GUIEventLogger(EventLogger):
    __metaclass__ = ABCMeta

    def __init__(self):
        super().__init__()
        self.cw = None

    @abstractmethod
    def get_widget(self) -> QWidget:
        raise NotImplementedError

    def set_chamber(self, cw: ChamberWidget) -> None:
        """
        Sets the GUI chamber that is related to this EventLogger.

        Parameters
        ----------
        cw : ChamberWidget
            The ChamberWidget that will be assigned to this EventLogger
        """
        self.cw = cw

