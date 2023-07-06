from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI
    from Components.Toggle import Toggle

import pygame
from Elements.draw_light import draw_light
from Elements.Element import Element
from GUIs import Colors


class CircleLightElement(Element):
    def __init__(self, tg: GUI, x: int, y: int, radius: int, on_color: tuple[int, int, int] = Colors.lightgray, background_color: tuple[int, int, int] = Colors.darkgray, comp: Toggle = None, SF: float = None):
        super().__init__(tg, x, y, pygame.Rect(x, y, radius * 2, radius * 2), SF)
        self.radius = int(self.SF * radius)
        self.on_color = on_color
        self.background_color = background_color
        self.off_color = (int(on_color[0] * .2), int(on_color[1] * .2), int(on_color[2] * .2))
        self.comp = comp
        self.on = comp.get_state()

    def has_updated(self) -> bool:
        return self.on != self.comp.get_state()

    def draw(self) -> None:
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.on = self.comp.get_state()

        if self.on:
            pygame.draw.circle(self.screen, self.on_color, (cx, cy), self.radius, 0)  # MAIN BULB
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), self.radius - 2, 1)  # white circle
            pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), self.radius + 2, 4)  # Black circle
        else:
            draw_light(self.screen, self.off_color, (0, 0, 0), self.rect, cx, cy, self.radius)

    def mouse_up_(self, event: pygame.event.Event) -> None:
        self.comp.toggle(not self.on)
