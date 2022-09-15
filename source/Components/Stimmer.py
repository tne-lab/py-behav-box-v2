from abc import ABCMeta
from Components.Component import Component


class Stimmer(Component):
    __metaclass__ = ABCMeta

    def parametrize(self, pnum, outs, per, dur, amps, durs):
        pass

    def start(self, pnum, stype):
        pass

    def get_state(self):
        pass

    def get_type(self):
        return Component.Type.OUTPUT
