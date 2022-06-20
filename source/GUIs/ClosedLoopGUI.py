from typing import List
from types import MethodType

from Elements.Element import Element
from Elements.FanElement import FanElement
from Elements.IndicatorElement import IndicatorElement
from GUIs import Colors
from GUIs.GUI import GUI


class ClosedLoopGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)

        def reward_available(self):
            return task.activated

        self.fan = FanElement(self.task_gui, self.SF * 210, self.SF * 20, self.SF * 40, task.fan)
        self.reward_indicator = IndicatorElement(self.task_gui, self.SF * 235, self.SF * 120, self.SF * 15, Colors.green,
                                                 Colors.red)
        self.reward_indicator.on = MethodType(reward_available, self.reward_indicator)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [self.fan, self.reward_indicator]
