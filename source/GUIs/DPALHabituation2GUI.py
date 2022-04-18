from typing import List
from types import MethodType

from source.Elements.CircleLightElement import CircleLightElement
from source.Elements.Element import Element
from source.Elements.NosePokeElement import NosePokeElement
from source.Elements.ButtonElement import ButtonElement
from source.Elements.InfoBoxElement import InfoBoxElement
from source.Elements.SoundElement import SoundElement
from source.Elements.FanElement import FanElement
from source.GUIs import Colors
from source.GUIs.GUI import GUI


class DPALHabituation2GUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def feed_mouse_up(self, _):
            self.clicked = False
            task.food.dispense()

        def pellets_text(self):
            return [str(task.food.pellets)]

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
