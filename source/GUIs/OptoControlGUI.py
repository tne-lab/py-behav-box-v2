from typing import List
from types import MethodType

from Elements.CircleLightElement import CircleLightElement
from Elements.Element import Element
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from GUIs.GUI import GUI


class OptoControlGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def complete_mouse_up(self, _):
            self.clicked = False
            task.complete = True

        def nstim_text(self):
            return [str(task.nstim)]

        def noff_text(self):
            return [str(task.noff)]

        def per_text(self):
            return [str(task.per)]

        def amp_text(self):
            return [str(task.amp)]

        def pw_text(self):
            return [str(task.pw)]

        self.fl = CircleLightElement(self, 50 + 25 + 60, 60, 30, comp=task.front_light)
        self.rl = CircleLightElement(self, 50 + 3 * (25 + 60), 60, 30, comp=task.rear_light)
        self.complete_button = ButtonElement(self, 225, 300, 50, 20, "FINISH")
        self.complete_button.mouse_up = MethodType(complete_mouse_up, self.complete_button)
        nstim = InfoBoxElement(self, 400, 250, 50, 15, "NSTIM", 'BOTTOM', ['0'])
        nstim.get_text = MethodType(nstim_text, nstim)
        self.info_boxes.append(nstim)
        noff = InfoBoxElement(self, 400, 300, 50, 15, "NOFF", 'BOTTOM', ['0'])
        noff.get_text = MethodType(noff_text, noff)
        self.info_boxes.append(noff)
        per = InfoBoxElement(self, 50, 200, 50, 15, "PERIOD", 'BOTTOM', ['0'])
        per.get_text = MethodType(per_text, per)
        self.info_boxes.append(per)
        amp = InfoBoxElement(self, 50, 250, 50, 15, "AMP", 'BOTTOM', ['0'])
        amp.get_text = MethodType(amp_text, amp)
        self.info_boxes.append(amp)
        pw = InfoBoxElement(self, 50, 300, 50, 15, "PW", 'BOTTOM', ['0'])
        pw.get_text = MethodType(pw_text, pw)
        self.info_boxes.append(pw)

    def get_elements(self) -> List[Element]:
        return [self.fl, self.rl, self.complete_button, *self.info_boxes]
