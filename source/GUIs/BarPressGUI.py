from typing import List
from types import MethodType
from enum import Enum
import math

from Elements.BarPressElement import BarPressElement
from Elements.Element import Element
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from Events.InputEvent import InputEvent
from GUIs import Colors
from GUIs.GUI import GUI


class BarPressGUI(GUI):
    class Inputs(Enum):
        GUI_PELLET = 0

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def feed_mouse_up(self, _):
            self.clicked = False
            task.food.dispense()
            task.events.append(InputEvent(task, BarPressGUI.Inputs.GUI_PELLET))

        def pellets_text(self):
            return [str(task.food.pellets)]

        def presses_text(self):
            return [str(task.presses)]

        def event_countup(self):
            return [str(round(task.time_elapsed() / 60, 2))]

        def vi_countdown(self):
            if task.state == task.States.REWARD_UNAVAILABLE:
                return [str(max([0, math.ceil(task.lockout - task.time_in_state())]))]
            else:
                return "0"

        self.lever = BarPressElement(self.task_gui, self.SF * 77, self.SF * 25, self.SF * 100, self.SF * 90, task.food_lever)
        self.feed_button = ButtonElement(self.task_gui, self.SF * 129, self.SF * 170, self.SF * 50, self.SF * 20, "FEED", task.food, int(self.SF * 12))
        self.feed_button.mouse_up = MethodType(feed_mouse_up, self.feed_button)
        presses = InfoBoxElement(self.task_gui, self.SF * 69, self.SF * 125, self.SF * 50, self.SF * 15, "PRESSES",
                                 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        presses.get_text = MethodType(presses_text, presses)
        self.info_boxes.append(presses)
        pellets = InfoBoxElement(self.task_gui, self.SF * 129, self.SF * 125, self.SF * 50, self.SF * 15, "PELLETS", 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        pellets.get_text = MethodType(pellets_text, pellets)
        self.info_boxes.append(pellets)
        ec = InfoBoxElement(self.task_gui, self.SF * 372, self.SF * 170, self.SF * 50, self.SF * 15, "TIME", 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        ec.get_text = MethodType(event_countup, ec)
        self.info_boxes.append(ec)
        vic = InfoBoxElement(self.task_gui, self.SF * 64, self.SF * 170, self.SF * 50, self.SF * 15, "VI COUNT",
                             'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        vic.get_text = MethodType(vi_countdown, vic)
        self.info_boxes.append(vic)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [self.feed_button, *self.info_boxes, self.lever]
