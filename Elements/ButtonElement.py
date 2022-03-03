import pygame

from Elements.Element import Element
from GUIs import Colors


class ButtonElement(Element):
    def __init__(self, screen, x, y, w, h, text, tc=None, f_size=12):
        super().__init__(screen, x, y, pygame.Rect(x-3, y-3, w+6, h+6))
        self.w = w
        self.h = h
        self.text = text
        self.f_size = f_size
        self.face = pygame.Rect(x, y, w, h)
        self.pt1 = x, y
        self.pt2 = x+w, y
        self.pt3 = x+w, y+h
        self.pt4 = x, y+h
        self.face_color = (150, 150, 150)
        self.clicked = False
        self.tc = tc

    def draw(self):
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
        my_font = pygame.font.SysFont('arial', self.f_size)
        msg_in_font = my_font.render(self.text, True, Colors.white)
        msg_ht = msg_in_font.get_height()
        msg_wd = msg_in_font.get_width()
        msg_x = (self.rect.width - msg_wd) / 2
        msg_y = (self.rect.height - msg_ht) / 2
        self.screen.blit(msg_in_font, self.rect.move(msg_x, msg_y))

    def mouse_up(self):
        self.clicked = False

    def mouse_down(self):
        self.clicked = True
