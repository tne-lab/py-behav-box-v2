import pygame

from Elements.draw_light import draw_light
from Elements.Element import Element
from GUIs import Colors


class IndicatorElement(Element):
    def __init__(self, tg, x, y, radius, on_color=Colors.green, off_color=Colors.red):
        super().__init__(tg, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = int(self.SF * radius)
        self.on_color = on_color
        self.off_color = off_color

    def on(self):
        return True

    def draw(self):
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y

        if self.on():
            draw_light(self.screen, self.on_color, (0, 0, 0), self.rect, cx, cy, self.radius)
        else:
            draw_light(self.screen, self.off_color, (0, 0, 0), self.rect, cx, cy, self.radius)
