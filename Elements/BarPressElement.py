import pygame as pygame
import math

from Elements.Element import Element
from GUIs import Colors


class BarPressElement(Element):
    def __init__(self, screen, x, y, w, h, lc=None):
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h))
        self.w = w
        self.h = h
        self.pressed = lc.get_state()
        self.lc = lc

    def draw(self):
        self.pressed = self.lc.get_state()
        pygame.draw.rect(self.screen, Colors.black, self.rect, 0)
        pygame.draw.rect(self.screen, Colors.gray, pygame.Rect(self.x + 2, self.y + 2, self.w - 4, self.h / 6), 0)
        if not self.pressed:
            pygame.draw.polygon(self.screen, Colors.lightgray,
                                [(self.x + 2, self.y + 2 + self.h / 6), (self.x + self.w - 4, self.y + 2 + self.h / 6), (
                                    self.x + self.w - 4 - 3 * self.h / 6 * math.tan(math.pi / 180 * 10),
                                    self.y + 2 + 4 * self.h / 6), (
                                     self.x + 2 - 3 * self.h / 6 * math.tan(math.pi / 180 * 10),
                                     self.y + 2 + 4 * self.h / 6)])
            pygame.draw.line(self.screen, Colors.white, (self.x + 2, self.y + 2 + self.h / 6),
                             (self.x + self.w - 4, self.y + 2 + self.h / 6))
            pygame.draw.rect(self.screen, Colors.gray,
                             pygame.Rect(self.x + 2 - 3 * self.h / 6 * math.tan(math.pi / 180 * 10),
                                         self.y + 2 + 4 * self.h / 6, self.w - 4, self.h / 6), 0)
        else:
            pygame.draw.rect(self.screen, Colors.lightgray, pygame.Rect(self.x + 2, self.y + 2 + self.h / 6, self.w - 4, 3 * self.h / 6), 0)
            pygame.draw.line(self.screen, Colors.white, (self.x + 2, self.y + 2 + self.h / 6),
                             (self.x + self.w - 4, self.y + 2 + self.h / 6))
            pygame.draw.rect(self.screen, Colors.gray,
                             pygame.Rect(self.x + 2, self.y + 2 + 4 * self.h / 6, self.w - 4, self.h / 6), 0)

    def mouse_up(self, event):
        self.pressed = False
        self.lc.toggle(self.pressed)

    def mouse_down(self, event):
        self.pressed = True
        self.lc.toggle(self.pressed)
