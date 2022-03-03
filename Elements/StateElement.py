from abc import ABCMeta, abstractmethod
from Elements.Element import Element


class StateElement(Element):
    __metaclass__ = ABCMeta

    def __init__(self, screen, x, y, rect, init_state):
        super().__init__(screen, x, y, rect)
        self.state = init_state

    @abstractmethod
    def draw(self):
        raise NotImplementedError
