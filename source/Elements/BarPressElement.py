import pygame as pygame
import math

from Elements.Element import Element
from GUIs import Colors


class BarPressElement(Element):
    def __init__(self, tg, x, y, w, h, comp=None):
        super().__init__(tg, x, y, pygame.Rect(x, y, w, h))
        self.w = int(self.SF * w)
        self.h = int(self.SF * h)
        self.pressed = comp.get_state()
        self.comp = comp

    def draw(self):
        self.pressed = self.comp.get_state()
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
        self.comp.toggle(self.pressed)

    def mouse_down(self, event):
        self.pressed = True
        self.comp.toggle(self.pressed)
