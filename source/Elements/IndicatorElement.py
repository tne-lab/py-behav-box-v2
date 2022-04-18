import pygame

from source.Elements.draw_light import draw_light
from source.Elements.Element import Element


class IndicatorElement(Element):
    def __init__(self, screen, x, y, radius, on_color, off_color):
        super().__init__(screen, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = radius
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
