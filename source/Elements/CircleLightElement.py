import pygame

from source.Elements.draw_light import draw_light
from source.Elements.Element import Element


class CircleLightElement(Element):
    def __init__(self, screen, x, y, radius, on_color, background_color, lc=None):
        super().__init__(screen, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = radius
        self.on_color = on_color
        self.background_color = background_color
        self.off_color = (int(on_color[0] * .2), int(on_color[1] * .2), int(on_color[2] * .2))
        self.lc = lc
        self.on = lc.get_state()

    def draw(self):
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.on = self.lc.get_state()

        if self.on:
            pygame.draw.circle(self.screen, self.on_color, (cx, cy), self.radius, 0)  # MAIN BULB
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), self.radius - 2, 1)  # white circle
            pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), self.radius + 2, 4)  # Black circle
        else:
            draw_light(self.screen, self.off_color, (0, 0, 0), self.rect, cx, cy, self.radius)

    def mouse_up(self, event):
        self.on = not self.on
        self.lc.toggle(self.on)
