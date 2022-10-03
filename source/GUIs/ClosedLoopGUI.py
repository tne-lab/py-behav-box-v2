from types import MethodType
from typing import List

from Elements.Element import Element
from Elements.FanElement import FanElement
from GUIs import Colors
from GUIs.GUI import GUI

from Elements.InfoBoxElement import InfoBoxElement


class ClosedLoopGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def total_pulses(self):
            if task.started:
                return [str(task.pulse_count)]
            else:
                return [str(0)]

        ne = InfoBoxElement(self, 372, 125, 50, 15, "Total Pulses", 'BOTTOM', ['0'])
        ne.get_text = MethodType(total_pulses, ne)
        self.info_boxes.append(ne)
        #self.fan = FanElement(self.task_gui, 210, 20, 40, comp=task.fan)

    def get_elements(self) -> List[Element]:
        return [*self.info_boxes]
