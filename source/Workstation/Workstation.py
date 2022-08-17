import importlib
from pkgutil import iter_modules
from inspect import isclass
import signal

import math
import atexit

from GUIs import *
from GUIs import Colors
from Elements.LabelElement import LabelElement
import pygame
from Workstation.WorkstationGUI import WorkstationGUI
from Tasks.TaskSequence import TaskSequence

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
        signal.signal(signal.SIGTERM, self.exit_handler)
        signal.signal(signal.SIGINT, self.exit_handler)
        sys.exit(app.exec())

    def add_task(self, chamber, task_name, address_file, protocol, task_event_loggers):
        """
        Creates a Task and adds it to the chamber.

        Parameters
        ----------
        chamber : int
            The index of the chamber where the task will be added
        task_name : string
            The name corresponding to the Task class
        address_file : string
            The file path for the Address File
        protocol : string
            The file path for the Protocol
        task_event_loggers : list
            The list of EventLoggers for the task
        """
        # Import the selected Task
        task_module = importlib.import_module("Tasks." + task_name)
        task = getattr(task_module, task_name)
        metadata = {"chamber": chamber, "subject": "default"}
        self.tasks[chamber] = task(self, metadata, self.sources, address_file, protocol)  # Create the task
        self.event_loggers[chamber] = task_event_loggers
        # Import the Task GUI
        gui = getattr(importlib.import_module("GUIs." + task_name + "GUI"), task_name + "GUI")
        # Position the GUI in pygame
        col = chamber % self.n_col
        row = math.floor(chamber / self.n_col)
        # Create the GUI
        self.guis[chamber] = gui(self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h),
                                 self.tasks[chamber])

    def switch_task(self, task_base, task_name, protocol=None):
        """
        Switch the active Task in a sequence.

        Parameters
        ----------
        task_base : Task
            The base Task of the sequence
        task_name : str
            The next Task in the sequence
        protocol : dict
            Dictionary representing the protocol for the new Task
        """
        task_module = importlib.import_module("Tasks." + task_name)
        task = getattr(task_module, task_name)
        # Create the new Task as part of a sequence
        new_task = task(task_base, task_base.components, protocol)
        gui = getattr(importlib.import_module("GUIs." + task_name + "GUI"), task_name + "GUI")
        # Position the GUI in pygame
        col = task_base.metadata['chamber'] % self.n_col
        row = math.floor(task_base.metadata['chamber'] / self.n_col)
        # Create the GUI
        self.guis[task_base.metadata['chamber']].sub_gui = gui(
            self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h),
            new_task)
        return new_task

    def remove_task(self, chamber, del_loggers=True):
        """
        Remove the Task from the specified chamber.

        Parameters
        ----------
        del_loggers
        chamber : int
            The chamber from which a Task should be removed
        """
        if del_loggers:
            for el in self.event_loggers[chamber]:  # Close all associated EventLoggers
                el.close()
        for c in self.tasks[chamber].components:
            c.close()
        del self.tasks[chamber]
        del self.event_loggers[chamber]
        del self.guis[chamber]

    def start_task(self, chamber):
        """
        Start the Task in the specified chamber.

        Parameters
        ----------
        chamber : int
            The chamber corresponding to the Task that should be started
        """
        self.tasks[chamber].start()  # Start the Task
        for el in self.event_loggers[chamber]:  # Start all EventLoggers and log initial events
            el.start()
            el.log_events(self.tasks[chamber].events)
        self.tasks[chamber].events = []

    def stop_task(self, chamber):
        """
        Stop the Task in the specified chamber.

        Parameters
        ----------
        chamber : int
            The chamber corresponding to the Task that should be stopped
        """
        self.tasks[chamber].stop()  # Stop the task
        for el in self.event_loggers[chamber]:  # Log remaining events
            el.log_events(self.tasks[chamber].events)
        self.tasks[chamber].events = []

    def loop(self):
        """
        Master event loop for all Tasks. Handles Task logic, GUI updates, and Task Events.
        """
        self.task_gui.fill(Colors.black)
        events = pygame.event.get()  # Get mouse/keyboard events
        for key in self.tasks:  # For each Task
            if self.tasks[key].started and not self.tasks[key].paused:  # If the Task has been started and is not paused
                self.tasks[key].main_loop()  # Run the Task's logic loop
                self.guis[key].handle_events(events)  # Handle mouse/keyboard events with the Task GUI
                self.log_events(key)  # Log Events with all associated EventLoggers
                if self.tasks[key].is_complete():  # Stop the Task if it is complete
                    self.wsg.chambers[key].stop()
            self.guis[key].draw()  # Update the GUI
            # Draw GUI border and subject name
            col = key % self.n_col
            row = math.floor(key / self.n_col)
            pygame.draw.rect(self.task_gui, Colors.white, pygame.Rect(col * self.w, row * self.h, self.w, self.h), 1)
            LabelElement(self.task_gui, col * self.w + 10, (row + 1) * self.h - 30, self.w, 20,
                         self.tasks[key].metadata["subject"]).draw()
        pygame.display.flip()  # Signal to pygame that the whole GUI has updated

    def log_events(self, chamber):
        for el in self.event_loggers[chamber]:
            el.log_events(self.tasks[chamber].events)
        self.tasks[chamber].events = []

    def exit_handler(self, *args):
        """
        Callback for when py-behav is closed.
        """
        for key in self.tasks:  # Stop all Tasks
            if self.tasks[key].started:
                self.stop_task(key)
        for src in self.sources:  # Close all Sources
            self.sources[src].close_source()
