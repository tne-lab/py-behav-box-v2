import importlib
from pkgutil import iter_modules
from inspect import isclass

import math
import atexit
import time

from GUIs import *
from GUIs import Colors
from Elements.LabelElement import LabelElement
import pygame
from Workstation.WorkstationGUI import WorkstationGUI

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os
import ast
from screeninfo import get_monitors


class Workstation:

    def __init__(self):
        self.tasks = {}
        self.event_loggers = {}

        # Core application details
        QCoreApplication.setOrganizationName("TNEL")
        QCoreApplication.setOrganizationDomain("tnelab.org")
        QCoreApplication.setApplicationName("Pybehav")

        # Load information from settings or set defaults
        settings = QSettings()
        # Store information on the available sources
        package_dir = "Sources/"
        for (_, module_name, _) in iter_modules([package_dir]):
            # import the module and iterate through its attributes
            module = importlib.import_module(f"Sources.{module_name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if isclass(attribute):
                    # Add the class to this package's variables
                    globals()[attribute_name] = attribute
        if settings.contains("sources"):
            self.sources = eval(settings.value("sources"))
        else:
            self.sources = {"es": EmptySource(), "etss": EmptyTouchScreenSource("(1024, 768)")}
            settings.setValue("sources", '{"es": EmptySource(), "etss": EmptyTouchScreenSource("(1024, 768)")}')
        # Store the number of available chambers
        if settings.contains("n_chamber"):
            self.n_chamber = int(settings.value("n_chamber"))
        else:
            self.n_chamber = 1
            settings.setValue("n_chamber", self.n_chamber)

        # Store the position of the pygame window
        if settings.contains("pygame/offset"):
            offset = ast.literal_eval(settings.value("pygame/offset"))
        else:
            m = get_monitors()[0]
            offset = (m.width / 6, 30)
            settings.setValue("pygame/offset", str(offset))

        os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % offset  # Position the pygame window
        pygame.init()
        pygame.display.set_caption("Pybehav")

        # Compute the arrangement of chambers in the pygame window
        if settings.contains("pygame/n_row"):
            self.n_row = int(settings.value("pygame/n_row"))
            self.n_col = int(settings.value("pygame/n_col"))
            self.w = int(settings.value("pygame/w"))
            self.h = int(settings.value("pygame/h"))
        else:
            szo = pygame.display.get_desktop_sizes()
            szo = szo[0]
            sz = (int(szo[0] * 5 / 6), int(szo[1] - 70))
            self.n_row = 1
            self.n_col = self.n_chamber
            self.w = sz[0] / self.n_chamber
            self.h = sz[0] / self.n_chamber * 2
            if self.h > sz[1]:
                self.h = sz[1]
                self.w = sz[1] / 2
            while self.h < sz[1] / (self.n_row + 1) or self.n_col * self.w > sz[0]:
                self.n_row += 1
                self.h = sz[1] / self.n_row
                self.w = self.h / 2
                self.n_col = math.ceil(self.n_chamber / self.n_row)
            settings.setValue("pygame/n_row", self.n_row)
            settings.setValue("pygame/n_col", self.n_col)
            settings.setValue("pygame/w", self.w)
            settings.setValue("pygame/h", self.h)
            settings.setValue("pyqt/w", int(szo[0] / 6))
            settings.setValue("pyqt/h", int(szo[1] - 70))

        self.task_gui = pygame.display.set_mode((self.w * self.n_col, self.h * self.n_row), pygame.RESIZABLE, 32)
        self.guis = {}
        app = QApplication(sys.argv)
        self.wsg = WorkstationGUI(self)
        atexit.register(self.exit_handler)
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
        for el in self.event_loggers[chamber]:
            el.close()
        del self.tasks[chamber]
        del self.event_loggers[chamber]

    def start_task(self, chamber):
        self.tasks[chamber].start()
        for el in self.event_loggers[chamber]:
            el.start()
            el.log_events(self.tasks[chamber].events)

    def stop_task(self, chamber):
        self.tasks[chamber].stop()
        for el in self.event_loggers[chamber]:
            el.log_events(self.tasks[chamber].events)
            el.close()

    # Should this be parallelized?
    def loop(self):
        self.task_gui.fill(Colors.black)
        events = pygame.event.get()
        for key in self.tasks:
            if self.tasks[key].started and not self.tasks[key].paused:
                self.tasks[key].main_loop()
                for el in self.event_loggers[key]:
                    el.log_events(self.tasks[key].events)
                self.guis[key].handle_events(events)
                if self.tasks[key].is_complete():
                    self.wsg.chambers[key].stop()
            self.guis[key].draw()
            col = key % self.n_col
            row = math.floor(key / self.n_col)
            pygame.draw.rect(self.task_gui, Colors.white, pygame.Rect(col * self.w, row * self.h, self.w, self.h), 1)
            LabelElement(self.task_gui, col * self.w + 10, (row + 1) * self.h - 30, self.w, 20, self.tasks[key].metadata["subject"]).draw()
        pygame.display.flip()

    def exit_handler(self):
        for key in self.tasks:
            if self.tasks[key].started:
                self.stop_task(key)
        for src in self.sources:
            self.sources[src].close_source()
