import pygame

from pybehave.Elements.Element import Element


class RectangleLightElement(Element):  # Not implemented
    def __init__(self, screen, x, y, w, h, on_color, background_color, lc=None):
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h))
        self.w = w
        self.h = h
        self.on_color = on_color
        self.background_color = background_color
        self.off_color = (int(on_color[0] * .2), int(on_color[1] * .2), int(on_color[2] * .2))
        self.lc = lc
        self.on = lc.get_state()

    def draw(self):
        self.on = self.lc.get_state()

        if self.on:
            pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(self.x - 2, self.y - 2, self.w + 4, self.h + 4), 0)
            pygame.draw.rect(self.screen, (255, 255, 255), self.rect, 0)
            pygame.draw.rect(self.screen, self.on_color, pygame.Rect(self.x + 2, self.y + 2, self.w - 4, self.h - 4), 0)
        else:
            pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(self.x - 2, self.y - 2, self.w + 4, self.h + 4), 0)
            pygame.draw.rect(self.screen, self.off_color, self.rect, 0)
            pygame.draw.circle(self.screen, (200, 200, 200), (self.x + self.w * 3 / 4, self.y + self.h * 1 / 4),
                               int(.05 * min([self.w, self.h])), 0)
            shadow_color = (int(self.off_color[0] * .8), int(self.off_color[1] * .8), int(self.off_color[2] * .8))
            shadow_w = int(0.1 * self.w)
            shadow_h = int(0.1 * self.h)
            if shadow_w > 15:
                shadow_w = 15
            if shadow_h > 15:
                shadow_h = 15
            pygame.draw.rect(self.screen, shadow_color, [self.x, self.y + self.h - shadow_h, self.w, shadow_h], 0)
            pygame.draw.rect(self.screen, shadow_color, [self.x, self.y, shadow_w, self.h], 0)

    def mouse_up(self, event):
        self.on = not self.on
        self.lc.toggle(self.on)
