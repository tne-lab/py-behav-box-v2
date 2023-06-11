from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI
    from Components.Toggle import Toggle

import pygame
import math

from Elements.Element import Element
from Elements.draw_filled_arc import draw_filled_arc
from GUIs import Colors


class FanElement(Element):

    def __init__(self, tg: GUI, x: int, y: int, radius: int, comp: Toggle = None):
        super().__init__(tg, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = int(self.SF * radius)
        self.comp = comp
        self.on = comp.get_state()

    def draw(self) -> None:
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.on = self.comp.get_state()
        sf = self.radius / 40
        if self.on:
            col = Colors.lightgray
        else:
            col = Colors.black
        pygame.draw.circle(self.screen, col, (cx, cy), 6 * sf, 3)
        draw_filled_arc(self.screen, (cx + (5 + 35 * sf / 2) / math.sqrt(2), cy + (5 + 35 * sf / 2) / math.sqrt(2)),
                        math.pi, 35 * sf / 2, -math.pi / 4, col)
        draw_filled_arc(self.screen, (cx + (5 + 35 * sf / 2) / math.sqrt(2), cy - (5 + 35 * sf / 2) / math.sqrt(2)),
                        math.pi, 35 * sf / 2, math.pi / 4, col)
        draw_filled_arc(self.screen, (cx - (5 + 35 * sf / 2) / math.sqrt(2), cy - (5 + 35 * sf / 2) / math.sqrt(2)),
                        math.pi, 35 * sf / 2, 3 * math.pi / 4, col)
        draw_filled_arc(self.screen, (cx - (5 + 35 * sf / 2) / math.sqrt(2), cy + (5 + 35 * sf / 2) / math.sqrt(2)),
                        math.pi, 35 * sf / 2, 5 * math.pi / 4, col)

    def has_updated(self) -> bool:
        return self.on != self.comp.get_state()

    def mouse_up(self, event: pygame.event.Event) -> None:
        self.comp.toggle(not self.on)
