import pygame as pygame

from Elements.Element import Element
from Elements.draw_light import draw_light
from GUIs import Colors


class FoodLightElement(Element):
    def __init__(self, screen, x, y, w, h, on_color, lc=None, line_color=Colors.black):
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h))
        self.on_color = on_color
        self.off_color = (int(on_color[0] * .2), int(on_color[1] * .2), int(on_color[2] * .2))
        self.line_color = line_color
        self.lc = lc
        self.on = lc.get_state()
        self.w = w
        self.h = h

    def draw(self):
        self.on = self.lc.get_state()
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

    def mouse_up(self, event):
        self.on = not self.on
        self.lc.toggle(self.on)
