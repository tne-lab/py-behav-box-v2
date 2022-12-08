from abc import ABCMeta, abstractmethod


class ScreenInterface:
    __metaclass__ = ABCMeta

    @abstractmethod
    def show(self):
        raise NotImplementedError

    @abstractmethod
    def hide(self):
        raise NotImplementedError