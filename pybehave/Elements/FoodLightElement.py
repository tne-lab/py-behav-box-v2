from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pybehave.GUIs.GUI import GUI
    from pybehave.Components.Toggle import Toggle

import pygame as pygame

from pybehave.Elements.Element import Element
from pybehave.Elements.draw_light import draw_light
from pybehave.GUIs import Colors


class FoodLightElement(Element):
    def __init__(self, tg: GUI, x: int, y: int, w: int, h: int, on_color: tuple[int, int, int] = Colors.lightgray, comp: Toggle = None, line_color: tuple[int, int, int] = Colors.black, SF: float = None):
        super().__init__(tg, x, y, pygame.Rect(x, y, w, h), SF)
        self.on_color = on_color
        self.off_color = (int(on_color[0] * .2), int(on_color[1] * .2), int(on_color[2] * .2))
        self.line_color = line_color
        self.comp = comp
        self.on = comp.get_state()
        self.w = self.SF * w
        self.h = self.SF * h

    def draw(self) -> None:
        self.on = self.comp.get_state()
        if self.on:
            pygame.draw.rect(self.screen, self.on_color, self.rect,  0)
            pygame.draw.rect(self.screen, self.line_color, self.rect, 1)
            pygame.draw.circle(self.screen, Colors.white, (self.x + self.w, self.y + self.h / 2), self.h / 8, 0)
            pygame.draw.circle(self.screen, Colors.white, (self.x, self.y + self.h / 2), self.h / 8, 0)
            pygame.draw.circle(self.screen, self.line_color, (self.x + self.w, self.y + self.h / 2), self.h / 8, 2)
            pygame.draw.circle(self.screen, self.line_color, (self.x, self.y + self.h / 2), self.h / 8, 2)
        else:
            pygame.draw.rect(self.screen, Colors.black, self.rect, 0)
            pygame.draw.rect(self.screen, self.line_color, self.rect, 1)
            draw_light(self.screen, self.off_color, (0, 0, 0),
                       pygame.Rect(self.x + self.w - self.h / 8, self.y + self.h / 2 - self.h / 8, self.h / 8 * 2,
                                   self.h / 8 * 2), self.x + self.w, self.y + self.h / 2, self.h / 8)
            draw_light(self.screen, self.off_color, (0, 0, 0),
                       pygame.Rect(self.x - self.h / 8, self.y + self.h / 2 - self.h / 8, self.h / 8 * 2,
                                   self.h / 8 * 2), self.x, self.y + self.h / 2, self.h / 8)

    def has_updated(self) -> bool:
        return self.on != self.comp.get_state()

    def mouse_up_(self, event: pygame.event.Event) -> None:
        self.comp.toggle(not self.on)
