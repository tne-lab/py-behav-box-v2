import pygame

from source.Elements.Element import Element


class InfoBoxElement(Element):

    def __init__(self, screen, x, y, w, h, label, label_pos, text, f_size=14, SF=1):  # passing SF is undesirable here
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h))
        self.label_pos = label_pos  # 'TOP','LEFT','RIGHT', or 'BOTTOM'
        self.surface_color = (255, 255, 255)
        bw = 2
        self.label = label
        self.text = text
        self.f_size = f_size
        self.border = pygame.Rect(x-bw, y-bw, w+2*bw, h+2*bw)
        self.pt1 = x, y
        self.pt2 = x+w, y
        self.pt3 = x+w, y+h
        self.pt4 = x, y+h
        self.SF = SF

    def get_text(self):
        return self.text

    def draw(self):
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
                msg_x = +5  # MULTIPLE LINE INFO BOX: Indent 5 pixels from box left

            ln_count = 0
            for line in self.text:
                msg_in_font = my_font.render(line, True, txt_color)
                msg_y = ln_count * msg_ht - 2
                self.screen.blit(msg_in_font, self.rect.move(msg_x,  msg_y+1))
                ln_count += 1
