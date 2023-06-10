from __future__ import annotations

import queue
import threading
import time
from typing import TYPE_CHECKING, List

from Tasks.TaskThread import TaskThread
from Tasks.TaskEvents import StopEvent, ClearEvent, HeartbeatEvent

if TYPE_CHECKING:
    from Events.EventLogger import EventLogger

import importlib
from pkgutil import iter_modules
from inspect import isclass
import signal

import math
import atexit

from GUIs import Colors
from Elements.LabelElement import LabelElement
import pygame

from Sources.EmptySource import EmptySource
from Sources.EmptyTouchScreenSource import EmptyTouchScreenSource
from Workstation.WorkstationGUI import WorkstationGUI
import Utilities.Exceptions as pyberror

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os
import ast
import traceback
from screeninfo import get_monitors


class Workstation:

    def __init__(self):
        self.task_threads = {}

        # Core application details
        QCoreApplication.setOrganizationName("TNEL")
        QCoreApplication.setOrganizationDomain("tnelab.org")
        QCoreApplication.setApplicationName("Pybehav")

        # Load information from settings or set defaults
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
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
            self.task_gui = pygame.display.set_mode((self.w * self.n_col, self.h * self.n_row), pygame.DOUBLEBUF | pygame.HWSURFACE, 32)
        else:
            self.compute_chambergui()

        self.ed = None
        app = QApplication(sys.argv)
        self.wsg = WorkstationGUI(self)
        self.gui_notifier = threading.Event()
        self.stopping = False
        heartbeat = threading.Thread(target=self.heartbeat)
        heartbeat.start()
        guithread = threading.Thread(target=self.gui_loop)
        guithread.start()
        gui_event_thread = threading.Thread(target=self.gui_event_loop)
        gui_event_thread.start()
        atexit.register(lambda: self.exit_handler())
        signal.signal(signal.SIGTERM, self.exit_handler)
        signal.signal(signal.SIGINT, self.exit_handler)
        sys.exit(app.exec())

    def compute_chambergui(self) -> None:
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        szo = pygame.display.get_desktop_sizes()
        szo = szo[0]
        sz = (int(szo[0] * 5 / 6), int(szo[1] - 70))
        self.n_row = 1
        self.n_col = self.n_chamber
        self.w = math.floor(sz[0] / self.n_chamber)
        self.h = math.floor(sz[0] / self.n_chamber * 2)
        if self.h > sz[1]:
            self.h = sz[1]
            self.w = math.floor(sz[1] / 2)
        while self.h < math.floor(sz[1] / (self.n_row + 1)) or self.n_col * self.w > sz[0]:
            self.n_row += 1
            self.h = math.floor(sz[1] / self.n_row)
            self.w = math.floor(self.h / 2)
            self.n_col = math.ceil(self.n_chamber / self.n_row)
        settings.setValue("pygame/n_row", self.n_row)
        settings.setValue("pygame/n_col", self.n_col)
        settings.setValue("pygame/w", self.w)
        settings.setValue("pygame/h", self.h)
        settings.setValue("pyqt/w", int(szo[0] / 6))
        settings.setValue("pyqt/h", int(szo[1] - 70))
        self.task_gui = pygame.display.set_mode((self.w * self.n_col, self.h * self.n_row), pygame.RESIZABLE, 32)

    def add_task(self, chamber: int, task_name: str, subject_name: str, address_file: str, protocol: str, task_event_loggers: List[EventLogger]) -> None:
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
        metadata = {"chamber": chamber, "subject": subject_name, "protocol": protocol, "address_file": address_file}
        try:
            self.task_threads[chamber] = TaskThread(self, task_name, metadata, queue.Queue(), task_event_loggers)  # Create the task
            self.task_threads[chamber].start()
        except BaseException as e:
            print(type(e).__name__)
            self.ed = QMessageBox()
            self.ed.setIcon(QMessageBox.Critical)
            self.ed.setWindowTitle("Error adding task")
            if isinstance(e, pyberror.ComponentRegisterError):
                self.ed.setText("A Component failed to register\n"+traceback.format_exc())
            elif isinstance(e, pyberror.SourceUnavailableError):
                self.ed.setText("A requested Source is currently unavailable")
            elif isinstance(e, pyberror.MalformedProtocolError):
                self.ed.setText("Error raised when parsing Protocol file\n"+traceback.format_exc())
            elif isinstance(e, pyberror.MalformedAddressFileError):
                self.ed.setText("Error raised when parsing AddressFile\n"+traceback.format_exc())
            elif isinstance(e, pyberror.InvalidComponentTypeError):
                self.ed.setText("A Component in the AddressFile is an invalid type")
            else:
                self.ed.setText("Unhandled exception\n"+traceback.format_exc())
            self.ed.setStandardButtons(QMessageBox.Ok)
            self.ed.show()
            raise pyberror.AddTaskError

    def remove_task(self, chamber: int, del_loggers: bool = True) -> threading.Thread:
        """
        Remove the Task from the specified chamber.

        Parameters
        ----------
        del_loggers
        chamber : int
            The chamber from which a Task should be removed
        """
        remove_thread = threading.Thread(target=lambda: self.remove_task_(chamber, del_loggers))
        remove_thread.start()
        return remove_thread

    def remove_task_(self, chamber: int, del_loggers: bool = True) -> None:
        if chamber in self.task_threads:
            self.task_threads[chamber].queue.put(ClearEvent(del_loggers), block=False)
            self.task_threads[chamber].join()
            del self.task_threads[chamber]

    def gui_event_loop(self) -> None:
        while not self.stopping:
            event = pygame.event.wait(500)
            if not event.type == pygame.NOEVENT:
                keys = list(self.task_threads.keys())
                handled = False
                for key in keys:
                    if key in self.task_threads and not self.task_threads[key].stopping:
                        handled = handled or self.task_threads[key].gui.handle_event(event)
                    elif key in self.task_threads and not self.task_threads[key].gui_events_disconnect.is_set():
                        self.task_threads[key].gui_events_disconnect.set()
                if handled:
                    self.gui_notifier.set()

    def gui_loop(self) -> None:
        while not self.stopping:
            self.gui_notifier.wait()
            self.gui_notifier.clear()
            self.task_gui.fill(Colors.black)
            keys = list(self.task_threads.keys())
            updates = []
            for key in keys:  # For each Task
                col = key % self.n_col
                row = math.floor(key / self.n_col)
                rect = pygame.Rect((col * self.w, row * self.h, self.w, self.h))
                if key in self.task_threads and not self.task_threads[key].stopping:
                    self.task_threads[key].gui.draw()  # Update the GUI
                    # Draw GUI border and subject name
                    # LabelElement(self.task_threads[key].gui, 10, self.h - 30, self.w, 20,
                    #             self.task_threads[key].metadata["subject"], SF=1).draw()
                    t = time.perf_counter()
                    updates.append(self.task_gui.blit(self.task_threads[key].gui.task_gui, rect))
                elif key in self.task_threads and not self.task_threads[key].gui_disconnect.is_set():
                    updates.append(rect)
                    self.task_threads[key].gui_disconnect.set()
            if len(updates) > 0:
                pygame.display.update(updates)  # Signal to pygame that the whole GUI has updated
            time.sleep(1/30)

    def heartbeat(self):
        while not self.stopping:
            keys = list(self.task_threads.keys())
            for key in keys:
                self.task_threads[key].queue.put(HeartbeatEvent(), block=False)
            time.sleep(1)

    def exit_handler(self, *args):
        """
        Callback for when py-behav is closed.
        """
        self.stopping = True
        for key in self.task_threads:  # Stop all Tasks
            if self.task_threads[key].task.started:
                self.task_threads[key].queue.put(StopEvent(), block=False)
            self.remove_task(key)
        for src in self.sources:  # Close all Sources
            self.sources[src].close_source()
