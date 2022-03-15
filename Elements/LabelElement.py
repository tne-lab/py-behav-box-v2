import pygame

from Elements.Element import Element


class LabelElement(Element):

    def __init__(self, screen, x, y, w, h, text, f_size=20):
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h))
        self.text = text
        self.f_size = f_size

    def draw(self):
        txt_color = (255, 255, 255)

        # WRITE LABEL text
        msg_font = pygame.font.SysFont('arial', self.f_size)
        msg_in_font = msg_font.render(self.text, True, txt_color)
        msg_ht = msg_in_font.get_height()
        msg_x = 0
        msg_y = (self.rect.height - msg_ht)/2
        self.screen.blit(msg_in_font, self.rect.move(msg_x,  msg_y+1))
