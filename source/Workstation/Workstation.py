from __future__ import annotations

import asyncio
import queue
import time
from typing import TYPE_CHECKING, List

from Events import PybEvents
from Events.LoggerEvent import LoggerEvent
from Utilities.create_task import create_task

if TYPE_CHECKING:
    from Events.EventLogger import EventLogger

import importlib
from pkgutil import iter_modules
from inspect import isclass
import signal

import math
import atexit

from GUIs import Colors
import pygame

from Sources.EmptySource import EmptySource
from Workstation.WorkstationGUI import WorkstationGUI
import Utilities.Exceptions as pyberror

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import ast
import traceback
from screeninfo import get_monitors
from line_profiler import LineProfiler


class Workstation:

    def __init__(self):
        self.tasks = {}
        self.task_event_loggers = {}
        self.guis = {}
        self.sources = {}
        self.n_chamber, self.n_col, self.n_row, self.w, self.h = 0, 0, 0, 0, 0
        self.ed = None
        self.wsg = None
        self.queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()
        self.gui_task = None
        self.gui_event_task = None
        self.main_task = None
        self.heartbeat_task = None
        self.delay_heartbeat = False
        self.fr = 10
        self.last_frame = 0
        self.task_gui = None
        self.gui_updates = []
        self.gui_queue = queue.Queue()
        self.refresh_gui = True
        # self.lp = LineProfiler()
        # self.gui_wrapper = self.lp(self.update_gui)

        # Core application details
        QCoreApplication.setOrganizationName("TNEL")
        QCoreApplication.setOrganizationDomain("tnelab.org")
        QCoreApplication.setApplicationName("Pybehav")

        # Load information from settings or set defaults
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
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
            self.task_gui = pygame.display.set_mode((self.w * self.n_col, self.h * self.n_row),
                                                    pygame.DOUBLEBUF | pygame.HWSURFACE, 32)
        else:
            self.compute_chambergui()

    async def start_workstation(self):
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
            for source in self.sources.values():
                await source.initialize()
        else:
            self.sources = {"es": EmptySource()}
            settings.setValue("sources", '{"es": EmptySource()}')
        # Store the number of available chambers
        if settings.contains("n_chamber"):
            self.n_chamber = int(settings.value("n_chamber"))
        else:
            self.n_chamber = 1
            settings.setValue("n_chamber", self.n_chamber)
        # Store the GUI refresh state
        if settings.contains("refresh_gui"):
            self.refresh_gui = bool(settings.value("refresh_gui"))
        else:
            self.refresh_gui = True
            settings.setValue("refresh_gui", self.refresh_gui)

        self.wsg = WorkstationGUI(self)
        self.gui_task = self.loop.run_in_executor(None, self.update_gui)
        self.gui_event_task = self.loop.run_in_executor(None, self.gui_event_loop)
        self.main_task = create_task(self.run())
        self.heartbeat_task = create_task(self.heartbeat())

        atexit.register(lambda: self.exit_handler())
        signal.signal(signal.SIGTERM, self.exit_handler)
        signal.signal(signal.SIGINT, self.exit_handler)

    async def run(self):
        while True:
            event = await self.queue.get()
            self.delay_heartbeat = True
            if isinstance(event, PybEvents.ExitEvent):
                return
            elif isinstance(event, PybEvents.StartEvent):
                for el in self.task_event_loggers[event.task.metadata["chamber"]]:  # Start all EventLoggers
                    el.start_()
                event.task.start__()
                new_event = PybEvents.StateEnterEvent(event.task, event.task.state, event.metadata)
                event.task.main_loop(new_event)
                self.log_event(new_event.format())
            elif isinstance(event, PybEvents.TaskCompleteEvent):
                self.wsg.chambers[event.task.metadata["chamber"]].stop()
                event.task.complete = True
            elif isinstance(event, PybEvents.StopEvent):
                new_event = PybEvents.StateExitEvent(event.task, event.task.state, event.metadata)
                event.task.main_loop(new_event)
                self.log_event(new_event.format())
                event.task.stop__()
                self.log_event(event.format())
            elif isinstance(event, PybEvents.PauseEvent):
                event.task.pause__()
                event.task.main_loop(event)
                self.log_event(event.format())
            elif isinstance(event, PybEvents.ResumeEvent):
                event.task.resume__()
                event.task.main_loop(event)
            elif isinstance(event, PybEvents.InitEvent):
                event.task.init()
            elif isinstance(event, PybEvents.ClearEvent):
                event.task.clear()
                del_loggers = event.del_loggers
                if del_loggers:
                    for logger in self.task_event_loggers[event.task.metadata["chamber"]]:
                        logger.close_()
                    del self.task_event_loggers[event.task.metadata["chamber"]]
                del self.tasks[event.task.metadata["chamber"]]
                del self.guis[event.task.metadata["chamber"]]
                event.done.set()
            elif isinstance(event, PybEvents.HeartbeatEvent):
                for key in self.tasks.keys():
                    if self.tasks[key].started and not self.tasks[key].paused:
                        self.tasks[key].main_loop(event)
                self.delay_heartbeat = False
            elif isinstance(event, PybEvents.ComponentUpdateEvent):
                comp = event.task.components[event.comp_id][0]
                if comp.update(event.value) and event.task.started and not event.task.paused:
                    if event.metadata is None:
                        event.metadata = {}
                    event.metadata["value"] = comp.state
                    new_event = PybEvents.ComponentChangedEvent(event.task, comp, event.metadata)
                    event.task.main_loop(new_event)
                    self.log_event(new_event.format())
                    if event.task.is_complete_():
                        self.queue.put_nowait(PybEvents.TaskCompleteEvent(event.task))
            elif isinstance(event, PybEvents.PygameEvent):
                handled = False
                for key in self.guis.keys():
                    handled = handled or self.guis[key].handle_event(event.event)
            elif isinstance(event, PybEvents.StatefulEvent):
                if event.task.started and not event.task.paused:
                    event.task.main_loop(event)
                    if event.task.is_complete_():
                        self.queue.put_nowait(PybEvents.TaskCompleteEvent(event.task))
            if isinstance(event, PybEvents.Loggable):
                if event.task.started and not event.task.paused:
                    self.log_event(event.format())
            if self.refresh_gui:
                self.gui_queue.put_nowait(event)
            # self.gui_wrapper(event)
            # self.lp.print_stats()

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

    async def add_task(self, chamber: int, task_name: str, subject_name: str, address_file: str, protocol: str, task_event_loggers: List[EventLogger]) -> None:
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
            task_module = importlib.import_module("Local.Tasks." + task_name)
            task = getattr(task_module, task_name)
            self.tasks[chamber] = task()
            await self.tasks[chamber].initialize(self, metadata, self.sources)  # Create the task
            self.task_event_loggers[chamber] = task_event_loggers
            for logger in task_event_loggers:
                logger.set_task(self.tasks[chamber])
            gui = getattr(importlib.import_module("Local.GUIs." + task_name + "GUI"), task_name + "GUI")
            # Position the GUI in pygame
            col = chamber % self.n_col
            row = math.floor(chamber / self.n_col)
            self.guis[chamber] = gui(self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h), self.tasks[chamber])
            self.queue.put_nowait(PybEvents.InitEvent(self.tasks[chamber]))
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

    def remove_task(self, chamber: int, del_loggers: bool = True) -> asyncio.Event:
        """
        Remove the Task from the specified chamber.

        Parameters
        ----------
        del_loggers
        chamber : int
            The chamber from which a Task should be removed
        """
        done = asyncio.Event()
        self.queue.put_nowait(PybEvents.ClearEvent(self.tasks[chamber], del_loggers, done))
        return done

    def gui_event_loop(self) -> None:
        while True:
            event = pygame.event.wait()
            asyncio.run_coroutine_threadsafe(self.queue.put(PybEvents.PygameEvent(event)), loop=self.loop)

    def update_gui(self) -> None:
        while True:
            event = self.gui_queue.get()
            if isinstance(event, PybEvents.TaskEvent):
                col = event.task.metadata["chamber"] % self.n_col
                row = math.floor(event.task.metadata["chamber"] / self.n_col)
                rect = pygame.Rect((col * self.w, row * self.h, self.w, self.h))
                if isinstance(event, PybEvents.InitEvent) or isinstance(event, PybEvents.TaskCompleteEvent) \
                        or isinstance(event, PybEvents.StartEvent):
                    self.guis[event.task.metadata["chamber"]].draw()
                    self.gui_updates.append(rect)
                elif isinstance(event, PybEvents.ClearEvent):
                    pygame.draw.rect(self.task_gui, Colors.black, rect)
                    self.gui_updates.append(rect)
                else:
                    for element in self.guis[event.task.metadata["chamber"]].get_elements():
                        if element.has_updated():
                            element.draw()
                            self.gui_updates.append(element.rect.move(col * self.w, row * self.h))
            elif isinstance(event, PybEvents.HeartbeatEvent):
                for key in self.guis.keys():
                    col = key % self.n_col
                    row = math.floor(key / self.n_col)
                    for element in self.guis[key].get_elements():
                        if element.has_updated():
                            element.draw()
                            self.gui_updates.append(element.rect.move(col * self.w, row * self.h))
            if time.perf_counter() - self.last_frame > 1 / self.fr:
                if len(self.gui_updates) > 0:
                    pygame.display.update(self.gui_updates)
                    self.gui_updates = []
                self.last_frame = time.perf_counter()

    async def heartbeat(self):
        while True:
            await asyncio.sleep(1 / self.fr)
            if self.delay_heartbeat:
                self.delay_heartbeat = False
            else:
                self.queue.put_nowait(PybEvents.HeartbeatEvent())

    def log_event(self, event: LoggerEvent):
        for logger in self.task_event_loggers[event.event.task.metadata["chamber"]]:
            logger.queue.put_nowait(event)

    def exit_handler(self, *args):
        self.loop.run_until_complete(self.exit_handler_())

    async def exit_handler_(self):  # Make async
        """
        Callback for when py-behav is closed.
        """
        self.heartbeat_task.cancel()
        self.gui_event_task.cancel()
        for chamber in self.tasks.keys():  # Stop all Tasks
            if self.tasks[chamber].started:
                self.queue.put_nowait(PybEvents.StopEvent(chamber))
            done = self.remove_task(chamber)
            await done.wait()
        self.queue.put_nowait(PybEvents.ExitEvent())
        await self.main_task
        self.gui_task.cancel()
        for src in self.sources:  # Close all Sources
            self.sources[src].close_source()
