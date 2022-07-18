from abc import ABCMeta, abstractmethod
from Components.Component import Component


class Stimmer(Component):
    __metaclass__ = ABCMeta

    @abstractmethod
    def parametrize(self, pnum, outs, per, dur, amps, durs): raise NotImplementedError

    @abstractmethod
    def start(self, pnum, stype): raise NotImplementedError

    @abstractmethod
    def get_state(self): raise NotImplementedError

    @abstractmethod
    def get_type(self): raise NotImplementedError
