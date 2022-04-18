import pygame
import math

from source.Elements.Element import Element
from source.Elements.draw_filled_arc import draw_filled_arc
from source.GUIs import Colors


class FanElement(Element):
    def __init__(self, screen, x, y, radius, tc=None):
        super().__init__(screen, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = radius
        self.tc = tc
        self.on = tc.get_state()

    def draw(self):
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.on = self.tc.get_state()
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

    def mouse_up(self, event):
        self.on = not self.on
        self.tc.toggle(self.on)
