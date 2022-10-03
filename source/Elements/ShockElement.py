import pygame

from Elements.Element import Element


class ShockElement(Element):
    def __init__(self, tg, x, y, radius, color=(255, 255, 0), comp=None):
        super().__init__(tg, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = int(self.SF * radius)
        self.color = color
        self.comp = comp
        self.on = comp.get_state()

    def draw(self):
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        self.on = self.comp.get_state()
        sf = self.radius / 23

        if self.on:
            col = (255, 0, 0)
        else:
            col = (0, 0, 0)
        pt1 = (cx - 2 * sf, cy - 15 * sf)
        pt2 = (cx - 6 * sf, cy - 5 * sf)
        pt3 = (cx - 3 * sf, cy - 5 * sf)
        pt4 = (cx - 8 * sf, cy + 5 * sf)
        pt5 = (cx - 5 * sf, cy + 5 * sf)
        pt6 = (cx - 10 * sf, cy + 15 * sf)

        pt7 = (cx, cy + 5 * sf)
        pt8 = (cx - 2 * sf, cy + 5 * sf)
        pt9 = (cx + 5 * sf, cy - 5 * sf)
        pt10 = (cx + 2 * sf, cy - 5 * sf)
        pt11 = (cx + 9 * sf, cy - 15 * sf)
        ptlist = [pt1, pt2, pt3, pt4, pt5, pt6, pt7, pt8, pt9, pt10, pt11]
        pygame.draw.polygon(self.screen, self.color, ptlist, 0)  # top white line
        pygame.draw.polygon(self.screen, (0, 0, 0), ptlist, 1)  # top white line
        pygame.draw.circle(self.screen, col, (cx, cy), self.radius, 2)

    def mouse_up(self, event):
        self.on = not self.on
        self.comp.toggle(self.on)
