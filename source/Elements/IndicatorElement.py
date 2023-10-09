from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI

import pygame

from Elements.draw_light import draw_light
from Elements.Element import Element
from GUIs import Colors


class IndicatorElement(Element):
    def __init__(self, tg: GUI, x: int, y: int, radius: int, on_color: tuple[int, int, int] = Colors.green, off_color: tuple[int, int, int] = Colors.red):
        super().__init__(tg, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = int(self.SF * radius)
        self.on_color = on_color
        self.off_color = off_color
        self.is_on = True

    def has_updated(self) -> bool:
        return self.is_on != self.on()

    # noinspection PyMethodMayBeStatic
    def on(self) -> bool:
        return self.is_on

    def draw(self) -> None:
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.is_on = self.on()

        if self.on():
            draw_light(self.screen, self.on_color, (0, 0, 0), self.rect, cx, cy, self.radius)
        else:
            draw_light(self.screen, self.off_color, (0, 0, 0), self.rect, cx, cy, self.radius)
