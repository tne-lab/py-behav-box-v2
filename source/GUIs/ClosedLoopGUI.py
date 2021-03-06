import math
from types import MethodType
from typing import List

from Elements.Element import Element
from Elements.FanElement import FanElement
from GUIs import Colors
from GUIs.GUI import GUI

from source.Elements.InfoBoxElement import InfoBoxElement


class ClosedLoopGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def total_pulses(self):
            if task.started:
                return [str(task.pulse_count)]
            else:
                return [str(0)]

        ne = InfoBoxElement(self.task_gui, self.SF * 372, self.SF * 125, self.SF * 50, self.SF * 15, "Total Pulses",
                            'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        ne.get_text = MethodType(total_pulses, ne)
        self.info_boxes.append(ne)
        self.fan = FanElement(self.task_gui, self.SF * 210, self.SF * 20, self.SF * 40, task.fan)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [self.fan, *self.info_boxes]
