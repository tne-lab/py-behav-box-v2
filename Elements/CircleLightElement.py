import pygame as pygame

from Elements.draw_light import draw_light
from Elements.StateElement import StateElement


class CircleLightElement(StateElement):
    def __init__(self, screen, x, y, radius, on_color, background_color, lc=None):
        super().__init__(screen, x, y, pygame.Rect(x, y, radius * 2, radius * 2), lc.get_state())
        self.radius = radius
        self.on_color = on_color
        self.background_color = background_color
        self.off_color = (int(on_color[0] * .2), int(on_color[1] * .2), int(on_color[2] * .2))
        self.lc = lc

    def draw(self):
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.state = self.lc.get_state()

        if self.state:
            pygame.draw.circle(self.screen, self.on_color, (cx, cy), self.radius, 0)  # MAIN BULB
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), self.radius - 2, 1)  # white circle
            pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), self.radius + 2, 4)  # Black circle
        else:
            draw_light(self.screen, self.off_color, (0, 0, 0), self.rect, cx, cy, self.radius)

    def mouse_up(self):
        self.state = not self.state
        self.lc.toggle(self.state)
