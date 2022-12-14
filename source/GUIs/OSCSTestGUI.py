import math
from types import MethodType
from typing import List

from Elements.Element import Element
from Elements.FanElement import FanElement
from Elements.IndicatorElement import IndicatorElement
from GUIs import Colors
from GUIs.GUI import GUI

from Elements.InfoBoxElement import InfoBoxElement


class OSCSTestGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def analog_in(self):
            return str(task.ain[0].get_state())

        def get_digital_in(self):
            return task.din.get_state()

        ne = InfoBoxElement(self, 372, 125, 50, 15, "NEXT EVENT", 'BOTTOM', ['0'])
        ne.get_text = MethodType(analog_in, ne)
        self.info_boxes.append(ne)
        self.digital_in = IndicatorElement(self, 74, 163, 15)
        self.digital_in.on = MethodType(get_digital_in, self.digital_in)

    def get_elements(self) -> List[Element]:
        return [self.digital_in, *self.info_boxes]
