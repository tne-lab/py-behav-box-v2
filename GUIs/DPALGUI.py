from typing import List
from types import MethodType

import pygame

from Elements.CircleLightElement import CircleLightElement
from Elements.RectangleLightElement import RectangleLightElement
from Elements.TouchScreenElement import TouchScreenElement
from Elements.Element import Element
from Elements.NosePokeElement import NosePokeElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from Elements.SoundElement import SoundElement
from Elements.FanElement import FanElement
from GUIs import Colors
from GUIs.GUI import GUI


class DPALGUI(GUI):

    def __init__(self, ws, task):
        super().__init__(ws, task)
        self.info_boxes = []

        def feed_mouse_up(self, _):
            self.clicked = False
            task.food.dispense()

        def pellets_text(self):
            return [str(task.food.pellets)]

        def trial_count_text(self):
            return [str(task.cur_trial+1)]

        self.touch_screen = TouchScreenElement(self.task_gui, 0, 0, 500, 375, pygame.Rect(0, 0, 500, 152), task.touch_screen)
        self.food_poke = NosePokeElement(self.task_gui, 220, 480, 30, task.init_poke)
        self.feed_button = ButtonElement(self.task_gui, 225, 600, 50, 20, "FEED", task.food)
        self.feed_button.mouse_up = MethodType(feed_mouse_up, self.feed_button)
        pellets = InfoBoxElement(self.task_gui, 225, 555, 50, 15, "PELLETS", 'BOTTOM', ['0'])
        pellets.get_text = MethodType(pellets_text, pellets)
        self.info_boxes.append(pellets)
        trial_count = InfoBoxElement(self.task_gui, 400, 600, 50, 15, "TRIAL", 'BOTTOM', ['0'])
        trial_count.get_text = MethodType(trial_count_text, trial_count)
        self.info_boxes.append(trial_count)
        self.food_light = CircleLightElement(self.task_gui, 220, 410, 30, Colors.lightgray, Colors.darkgray, task.init_light)
        self.cage_light = RectangleLightElement(self.task_gui, 350, 440, 80, 80, Colors.lightgray, Colors.darkgray, task.cage_light)
        self.tone = SoundElement(self.task_gui, 70, 430, 40, task.tone)
        self.fan = FanElement(self.task_gui, 70, 530, 40, task.fan)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()
        for touch in self.task.touch_screen.handled_touches:
            self.touch_screen.draw_plus_sign(touch, 3, Colors.green)
        pygame.display.flip()

    def get_elements(self) -> List[Element]:
        return [self.food_poke, self.food_light, self.touch_screen, self.feed_button, *self.info_boxes, self.tone, self.cage_light, self.fan]
