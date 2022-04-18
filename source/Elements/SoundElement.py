import pygame

from source.Elements.Element import Element


class SoundElement(Element):
    def __init__(self, screen, x, y, radius, sc=None):
        super().__init__(screen, x, y, pygame.Rect(x, y, radius * 2, radius * 2))
        self.radius = radius
        self.sc = sc
        self.on = sc.get_state()

    def draw(self):
        cx = self.x + self.radius  # center x
        cy = self.y + self.radius  # center y
        sf = self.radius / 40
        self.on = self.sc.get_state()

        if self.on:
            col = (0, 255, 0)
        else:
            col = (0, 0, 0)
        pygame.draw.circle(self.screen, col, (cx, cy), self.radius, 2)
        incr = 0
        for c in range(4):
            pygame.draw.circle(self.screen, col, (cx - 23 * sf + incr, cy - 15 * sf), 5 * sf, 1)
            incr += 15 * sf
        incr = 0
        for c in range(5):
            pygame.draw.circle(self.screen, col, (cx - 30 * sf + incr, cy), 5 * sf, 1)
            incr += 15 * sf
        incr = 0
        for c in range(4):
            pygame.draw.circle(self.screen, col, (cx - 23 * sf + incr, cy + 15 * sf), 5 * sf, 1)
            incr += 15 * sf
