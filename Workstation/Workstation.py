import importlib
import threading
import math
import time

from GUIs import *
from GUIs import Colors
from Elements.LabelElement import LabelElement
import pygame
from Workstation.WorkstationGUI import WorkstationGUI

from Sources.DIOSource import DIOSource
from Sources.EmptySource import EmptySource
from Sources.WhiskerTouchScreenSource import WhiskerTouchScreenSource
from Sources.EmptyTouchScreenSource import EmptyTouchScreenSource

from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
from screeninfo import get_monitors


class Workstation:

    def __init__(self):
        self.sources = {"es": EmptySource(), "etss": EmptyTouchScreenSource((1024, 768))}
        self.tasks = {}
        self.event_loggers = {}
        self.n_chamber = 5
        m = get_monitors()[0]
        os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % (m.width / 6, 30)
        pygame.init()
        pygame.display.set_caption("Pybehav")
        szo = pygame.display.get_desktop_sizes()
        szo = szo[0]
        sz = (int(szo[0] * 5 / 6), int(szo[1] - 70))
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
        app = QApplication(sys.argv)
        self.wsg = WorkstationGUI(self, szo)
        sys.exit(app.exec())

    def add_task(self, chamber, task_name, sources, address_file, protocol, task_event_loggers):
        task_module = importlib.import_module("Tasks." + task_name)
        task = getattr(task_module, task_name)
        metadata = {"chamber": chamber, "subject": "default"}
        self.tasks[chamber] = task(metadata, sources, address_file, protocol)
        self.event_loggers[chamber] = task_event_loggers
        gui = getattr(importlib.import_module("GUIs." + task_name + "GUI"), task_name + "GUI")
        col = chamber % self.n_col
        row = math.floor(chamber / self.n_col)
        self.guis[chamber] = gui(self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h),
                                 self.tasks[chamber])

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
            if self.tasks[key].started and not self.tasks[key].paused:
                self.tasks[key].main_loop()
                self.event_loggers[key].log_events(self.tasks[key].events)
                self.guis[key].handle_events(events)
            self.guis[key].draw()
            col = key % self.n_col
            row = math.floor(key / self.n_col)
            pygame.draw.rect(self.task_gui, Colors.white, pygame.Rect(col * self.w, row * self.h, self.w, self.h), 1)
            LabelElement(self.task_gui, col * self.w + 10, (row + 1) * self.h - 30, self.w, 20, self.tasks[key].metadata["subject"]).draw()
        pygame.display.flip()

