from typing import List
from types import MethodType

from Elements.CircleLightElement import CircleLightElement
from Elements.Element import Element
from Elements.NosePokeElement import NosePokeElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from GUIs import Colors
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

        def amp_text(self):
            return [str(task.amp)]

        def pw_text(self):
            return [str(task.pw)]

        self.fl = CircleLightElement(self.task_gui, self.SF * (50 + 25 + 60), self.SF * 60, self.SF * 30,
                                     Colors.lightgray, Colors.darkgray, task.front_light)
        self.rl = CircleLightElement(self.task_gui, self.SF * (50 + 3 * (25 + 60)), self.SF * 60, self.SF * 30,
                                     Colors.lightgray, Colors.darkgray, task.rear_light)
        self.complete_button = ButtonElement(self.task_gui, self.SF * 225, self.SF * 300, self.SF * 50, self.SF * 20,
                                             "FINISH", None, int(self.SF * 12))
        self.complete_button.mouse_up = MethodType(complete_mouse_up, self.complete_button)
        nstim = InfoBoxElement(self.task_gui, self.SF * 400, self.SF * 250, self.SF * 50, self.SF * 15, "NSTIM",
                               'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        nstim.get_text = MethodType(nstim_text, nstim)
        self.info_boxes.append(nstim)
        noff = InfoBoxElement(self.task_gui, self.SF * 400, self.SF * 300, self.SF * 50, self.SF * 15, "NOFF", 'BOTTOM',
                              ['0'], int(self.SF * 14), self.SF)
        noff.get_text = MethodType(noff_text, noff)
        self.info_boxes.append(noff)
        amp = InfoBoxElement(self.task_gui, self.SF * 50, self.SF * 250, self.SF * 50, self.SF * 15, "AMP",
                             'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        amp.get_text = MethodType(amp_text, amp)
        self.info_boxes.append(amp)
        pw = InfoBoxElement(self.task_gui, self.SF * 50, self.SF * 300, self.SF * 50, self.SF * 15, "PW",
                            'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        pw.get_text = MethodType(pw_text, pw)
        self.info_boxes.append(pw)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [self.fl, self.rl, self.complete_button, *self.info_boxes]
