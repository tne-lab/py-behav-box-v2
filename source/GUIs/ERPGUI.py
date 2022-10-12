import math
from types import MethodType
from typing import List

from Elements.Element import Element
from Elements.FanElement import FanElement
from GUIs import Colors
from GUIs.GUI import GUI

from Elements.InfoBoxElement import InfoBoxElement


class ERPGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def pulses_remaining(self):
            if task.started:
                return [str(task.npulse - task.pulse_count)]
            else:
                return [str(0)]

        ne = InfoBoxElement(self, 372, 125, 50, 15, "PULSES REMAINING", 'BOTTOM', ['0'])
        ne.get_text = MethodType(pulses_remaining, ne)
        self.info_boxes.append(ne)

    def get_elements(self) -> List[Element]:
        return [*self.info_boxes]
