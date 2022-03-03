from abc import ABCMeta, abstractmethod

import pygame.event


class GUI:
    __metaclass__ = ABCMeta

    def __init__(self, ws, task):
        self.task_gui = ws.task_gui
        self.task = task

    @abstractmethod
    def draw(self):
        raise NotImplementedError

    @abstractmethod
    def get_elements(self):
        raise NotImplementedError

    def handle_events(self):
        for event in pygame.event.get():
            for el in self.get_elements():
                el.handle_event(event)
