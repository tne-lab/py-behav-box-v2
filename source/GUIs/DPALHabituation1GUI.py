from typing import List

from source.Elements.Element import Element
from source.Elements.FanElement import FanElement
from source.GUIs import Colors
from source.GUIs.GUI import GUI


class DPALHabituation1GUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.fan = FanElement(self.task_gui, self.SF * 210, self.SF * 20, self.SF * 40, task.fan)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [self.fan]
