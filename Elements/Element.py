from abc import ABCMeta, abstractmethod

import pygame


class Element:
    __metaclass__ = ABCMeta

    def __init__(self, screen, x, y, rect):
        self.screen = screen
        self.x = x
        self.y = y
        self.rect = rect
        self._mouse_down = None
        self._mouse_up = None
        self.selected = False

    def mouse_down(self):
        pass

    def mouse_up(self):
        pass

    def handle_event(self, event):
        cur_x, cur_y = pygame.mouse.get_pos()
        match event.type:
            case pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.rect.collidepoint(cur_x, cur_y):
                    self.selected = True
                if self.mouse_down is not None and self.rect.collidepoint(cur_x, cur_y):
                    self.mouse_down()
                    return True
            case pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.rect.collidepoint(cur_x, cur_y) and self.selected:
                    if self.mouse_up is not None:
                        self.mouse_up()
                        self.selected = False
                        return True
                self.selected = False
        return False

    @abstractmethod
    def draw(self):
        raise NotImplementedError
