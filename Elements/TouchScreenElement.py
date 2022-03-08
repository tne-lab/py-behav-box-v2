import pygame as pygame

from Elements.Element import Element
from GUIs import Colors


class TouchScreenElement(Element):
    def __init__(self, screen, x, y, w, h, active_rect, tsc=None):
        super().__init__(screen, x, y, pygame.Rect(x, y, w, h))
        self.w = w
        self.h = h
        self.images = []
        self.active_rect = active_rect
        self.sf = w / tsc.display_size[0]
        self.tsc = tsc

    def draw(self):
        pygame.draw.rect(self.screen, Colors.darkgray, self.rect, 0)
        pygame.draw.rect(self.screen, Colors.black, self.active_rect, 0)
        for ic in self.tsc.image_containers.keys():
            img = pygame.image.load(ic)
            img = pygame.transform.scale(img, (self.tsc.image_containers[ic]["dim"][0] * self.sf, self.tsc.image_containers[ic]["dim"][1] * self.sf))
            img_rect = img.get_rect()
            coords = self.tsc.image_containers[ic]["coords"]
            img_rect = img_rect.move((coords[0] * self.sf, coords[1] * self.sf))
            self.screen.blit(img, img_rect)
        pygame.draw.rect(self.screen, Colors.black, self.rect, 3)

    def draw_plus_sign(self, coords, w, color):
        x = coords[0]
        y = coords[1]
        pygame.draw.line(self.screen, color, (x*self.sf - w, y*self.sf), (x*self.sf + w, y*self.sf), 1)
        pygame.draw.line(self.screen, color, (x*self.sf, y*self.sf - w), (x*self.sf, y*self.sf + w), 1)

    def mouse_up(self, event):
        cur_x, cur_y = pygame.mouse.get_pos()
        self.tsc.add_touch((cur_x / self.sf, cur_y / self.sf))
