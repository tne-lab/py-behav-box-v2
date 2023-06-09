from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI

import pygame
from Elements.Element import Element
from GUIs import Colors


class ButtonElement(Element):
    def __init__(self, tg: GUI, x: int, y: int, w: int, h: int, text: str, f_size: int = 12, SF: float = None):
        super().__init__(tg, x, y, pygame.Rect(x-3, y-3, w+6, h+6), SF)
        self.w = int(self.SF * w)
        self.h = int(self.SF * h)
        self.text = text
        self.f_size = int(self.SF * f_size)
        self.face = pygame.Rect(self.x, self.y, self.w, self.h)
        self.pt1 = self.x, self.y
        self.pt2 = self.x+self.w, self.y
        self.pt3 = self.x+self.w, self.y+self.h
        self.pt4 = self.x, self.y+self.h
        self.face_color = (150, 150, 150)
        self.clicked = False
        self.font = pygame.font.SysFont('arial', self.f_size)
        self._msg = self.font.render(self.text, True, Colors.white)

    def draw(self) -> None:
        ln_color = Colors.black
        # draw box
        pygame.draw.rect(self.screen, ln_color, self.rect)
        if self.clicked:
            pygame.draw.rect(self.screen, (100, 100, 100), self.face)
        else:
            pygame.draw.rect(self.screen, self.face_color, self.face)
            # Highlight
            pygame.draw.line(self.screen, (255, 255, 255), self.pt1, self.pt2)
            pygame.draw.line(self.screen, (255, 255, 255), self.pt2, self.pt3)
        pygame.draw.line(self.screen, (100, 100, 100), self.pt1, self.pt2)
        pygame.draw.line(self.screen, (100, 100, 100), self.pt2, self.pt3)
        # WRITE LABEL
        msg_ht = self._msg.get_height()
        msg_wd = self._msg.get_width()
        msg_x = (self.rect.width - msg_wd) / 2
        msg_y = (self.rect.height - msg_ht) / 2
        self.screen.blit(self._msg, self.rect.move(msg_x, msg_y))

    def mouse_up(self, event: pygame.event.Event) -> None:
        self.clicked = False

    def mouse_down(self, _) -> None:
        self.clicked = True
