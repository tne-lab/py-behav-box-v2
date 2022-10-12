from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from GUIs.GUI import GUI

import pygame

from Elements.Element import Element


class InfoBoxElement(Element):

    def __init__(self, screen: GUI, x: int, y: int, w: int, h: int, label: str, label_pos: str, text: str, f_size: int = 14, SF: float = None):
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h), SF)
        self.label_pos = label_pos  # 'TOP','LEFT','RIGHT', or 'BOTTOM'
        self.surface_color = (255, 255, 255)
        bw = int(self.SF*2)
        self.label = label
        self.text = text
        self.f_size = int(self.SF * f_size)
        w = self.SF * w
        h = self.SF * h
        self.border = pygame.Rect(self.x-bw, self.y-bw, w+2*bw, h+2*bw)
        self.pt1 = self.x, self.y
        self.pt2 = self.x+w, self.y
        self.pt3 = self.x+w, self.y+h
        self.pt4 = self.x, self.y+h

    def get_text(self) -> str:
        return self.text

    def draw(self) -> None:
        self.text = self.get_text()
        # Draw Box
        pygame.draw.rect(self.screen, (0, 0, 0), self.border)
        pygame.draw.rect(self.screen, (255, 255, 255), self.rect)
        txt_color = (0, 0, 0)

        # WRITE LABEL
        my_font = pygame.font.SysFont('arial', self.f_size, bold=True)
        lbl_in_font = my_font.render(self.label, True, (0, 0, 0))
        lbl_ht = lbl_in_font.get_height()
        lbl_wd = lbl_in_font.get_width()
        if self.label_pos == 'BOTTOM':
            lbl_x = (self.rect.width - lbl_wd)/2  # Center in box
            lbl_y = + 20 * self.SF  # Below Box
        elif self.label_pos == 'TOP':
            lbl_x = (self.rect.width - lbl_wd)/2  # Center in box
            lbl_y = - 20 * self.SF  # Above box
        elif self.label_pos == 'LEFT':
            lbl_x = - lbl_wd - 5 * self.SF
            lbl_y = (self.rect.height - lbl_ht)/2
        else:
            lbl_x = self.w + 5 * self.SF
            lbl_y = (self.rect.height - lbl_ht)/2

        self.screen.blit(lbl_in_font, self.rect.move(lbl_x,  lbl_y+1))

        # WRITE TEXT
        lines_in_txt = len(self.text)
        if lines_in_txt > 0:  # NOT EMPTY BOX, No info_boxes
            my_font = pygame.font.SysFont('arial', self.f_size)
            msg_in_font = my_font.render(self.text[0], True, (0, 0, 0))
            msg_ht = msg_in_font.get_height()
            msg_wd = msg_in_font.get_width()

            if lines_in_txt == 1:  # simple info box
                msg_x = (self.rect.width - msg_wd)/2  # Center in box
            else:  # lines_in_txt > 1:
                msg_x = +5 * self.SF  # MULTIPLE LINE INFO BOX: Indent 5 pixels from box left

            ln_count = 0
            for line in self.text:
                msg_in_font = my_font.render(line, True, txt_color)
                msg_y = ln_count * msg_ht - 2 * self.SF
                self.screen.blit(msg_in_font, self.rect.move(msg_x,  msg_y+1))
                ln_count += 1
