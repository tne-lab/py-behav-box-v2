from abc import ABCMeta, abstractmethod
from Events.EventLogger import EventLogger


class GUIEventLogger(EventLogger):
    __metaclass__ = ABCMeta

    def __init__(self):
        super().__init__()
        self.cw = None

    @abstractmethod
    def close(self): raise NotImplementedError

    @abstractmethod
    def log_events(self, events): raise NotImplementedError

    @abstractmethod
    def get_widget(self): raise NotImplementedError

    def set_chamber(self, cw):
        """
        Sets the GUI chamber that is related to this EventLogger.

        Parameters
        ----------
        cw : ChamberWidget
            The ChamberWidget that will be assigned to this EventLogger
        """
        self.cw = cw

