from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI
    from Components.Toggle import Toggle

import pygame

from Elements.Element import Element


class SoundElement(Element):
    def __init__(self, tg: GUI, x: int, y: int, radius: int, comp: Toggle = None):
        super().__init__(tg, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = int(self.SF * radius)
        self.comp = comp
        self.on = comp.get_state()

    def draw(self):
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        sf = self.radius / 40
        self.on = self.comp.get_state()

        if self.on:
            col = (0, 255, 0)
        else:
            col = (0, 0, 0)
        pygame.draw.circle(self.screen, col, (cx, cy), self.radius, 2)
        incr = 0
        for c in range(4):
            pygame.draw.circle(self.screen, col, (cx - 23 * sf + incr, cy - 15 * sf), 5 * sf, 1)
            incr += 15 * sf
        incr = 0
        for c in range(5):
            pygame.draw.circle(self.screen, col, (cx - 30 * sf + incr, cy), 5 * sf, 1)
            incr += 15 * sf
        incr = 0
        for c in range(4):
            pygame.draw.circle(self.screen, col, (cx - 23 * sf + incr, cy + 15 * sf), 5 * sf, 1)
            incr += 15 * sf

    def has_updated(self) -> bool:
        return self.on != self.comp.get_state()

    def mouse_up(self, event: pygame.event.Event) -> None:
        self.comp.toggle(not self.on)
