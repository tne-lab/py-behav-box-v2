import importlib
import threading
import math

from GUIs import *
from GUIs import Colors
import pygame


class Workstation:

    def __init__(self):
        self.tasks = {}
        self.event_loggers = {}
        self.n_chamber = 5
        pygame.init()
        sz = pygame.display.get_desktop_sizes()
        sz = sz[0]
        sz = (sz[0], sz[1] - 60)
        self.n_row = 1
        self.n_col = self.n_chamber
        self.w = sz[0] / self.n_chamber
        self.h = sz[0] / self.n_chamber * 2
        while self.h < sz[1] / (self.n_row + 1) or self.n_col * self.w > sz[0]:
            self.n_row += 1
            self.h = sz[1] / self.n_row
            self.w = self.h / 2
            self.n_col = math.ceil(self.n_chamber / self.n_row)
        self.task_gui = pygame.display.set_mode((self.w * self.n_col, self.h * self.n_row), pygame.SHOWN, 32)
        self.guis = {}

    def add_task(self, chamber, task_name, sources, address_file, protocol, task_event_loggers):
        task_module = importlib.import_module("Tasks."+task_name)
        task = getattr(task_module, task_name)
        self.tasks[chamber] = task(chamber, sources, address_file, protocol)
        self.event_loggers[chamber] = task_event_loggers
        gui = getattr(importlib.import_module("GUIs." + task_name + "GUI"), task_name + "GUI")
        col = chamber % self.n_col
        row = math.floor(chamber / self.n_col)
        self.guis[chamber] = gui(self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h), self.tasks[chamber])

    def remove_task(self, chamber):
        self.tasks[chamber].stop()
        self.event_loggers[chamber].close()
        del self.tasks[chamber]
        del self.event_loggers[chamber]

    def start_task(self, chamber):
        self.tasks[chamber].start()

    # Should this be parallelized?
    def loop(self):
        events = pygame.event.get()
        for key in self.tasks:
            if self.tasks[key].started:
                self.tasks[key].main_loop()
                self.event_loggers[key].log_events(self.tasks[key].events)
                self.guis[key].handle_events(events)
                self.guis[key].draw()
                col = key % self.n_col
                row = math.floor(key / self.n_col)
                pygame.draw.rect(self.task_gui, Colors.white, pygame.Rect(col * self.w, row * self.h, self.w, self.h), 1)
        pygame.display.flip()
