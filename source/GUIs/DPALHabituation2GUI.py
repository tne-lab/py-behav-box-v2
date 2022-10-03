from typing import List
from types import MethodType

from Elements.CircleLightElement import CircleLightElement
from Elements.Element import Element
from Elements.NosePokeElement import NosePokeElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from Elements.SoundElement import SoundElement
from Elements.FanElement import FanElement
from GUIs import Colors
from GUIs.GUI import GUI


class DPALHabituation2GUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def feed_mouse_up(self, _):
            self.clicked = False
            task.food.toggle(task.dispense_time)

        def pellets_text(self):
            return [str(task.food.count)]

        self.food_poke = NosePokeElement(self.task_gui, self.SF * 220, self.SF * 90, self.SF * 30, task.init_poke)
        self.feed_button = ButtonElement(self.task_gui, self.SF * 225, self.SF * 210, self.SF * 50, self.SF * 20, "FEED", task.food, int(self.SF * 12))
        self.feed_button.mouse_up = MethodType(feed_mouse_up, self.feed_button)
        pellets = InfoBoxElement(self.task_gui, self.SF * 225, self.SF * 165, self.SF * 50, self.SF * 15, "PELLETS", 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        pellets.get_text = MethodType(pellets_text, pellets)
        self.info_boxes.append(pellets)
        self.food_light = CircleLightElement(self.task_gui, self.SF * 220, self.SF * 20, self.SF * 30, Colors.lightgray, Colors.darkgray, task.init_light)
        self.tone = SoundElement(self.task_gui, self.SF * 70, self.SF * 50, self.SF * 40, task.tone)
        self.fan = FanElement(self.task_gui, self.SF * 70, self.SF * 140, self.SF * 40, task.fan)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [self.food_poke, self.food_light, self.feed_button, *self.info_boxes, self.tone, self.fan]
