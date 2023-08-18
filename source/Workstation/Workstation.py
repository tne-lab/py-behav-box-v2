from __future__ import annotations

import multiprocessing
import sys
import threading
import time
from multiprocessing.dummy.connection import Connection
from typing import TYPE_CHECKING, Type, List

import msgspec

from Events import PybEvents
from Events.EventWidget import EventWidget
from GUIs.SequenceGUI import SequenceGUI
from Tasks.TaskProcess import TaskProcess
from Workstation.WorkstationGUI import WorkstationGUI

if TYPE_CHECKING:
    from Tasks.Task import Task

import importlib

import math

from GUIs import Colors
import pygame

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import os
import ast
from screeninfo import get_monitors


class Workstation:

    def __init__(self):
        self.tasks = {}
        self.task_event_loggers = {}
        self.guis = {}
        self.sources = {}
        self.n_chamber, self.n_col, self.n_row, self.w, self.h = 0, 0, 0, 0, 0
        self.ed = None
        self.wsg = None
        self.mainq = None
        self.gui_task = None
        self.gui_event_task = None
        self.heartbeat_task = None
        self.delay_heartbeat = False
        self.fr = 10
        self.last_frame = 0
        self.task_gui = None
        self.gui_updates = []
        self.gui_queue = None
        self.qui_events_queue = None
        self.refresh_gui = True
        self.tp = None
        self.encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)
        self.decoder = msgspec.msgpack.Decoder(type=List[PybEvents.subclass_union(PybEvents.PybEvent)], dec_hook=PybEvents.dec_hook)

        # Core application details
        QCoreApplication.setOrganizationName("TNEL")
        QCoreApplication.setOrganizationDomain("tnelab.org")
        QCoreApplication.setApplicationName("Pybehave")

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
        pygame.display.set_caption("Pybehave")

        # Store the GUI refresh state
        if settings.contains("refresh_gui"):
            self.refresh_gui = bool(settings.value("refresh_gui"))
        else:
            self.refresh_gui = True
            settings.setValue("refresh_gui", self.refresh_gui)

        # Store the number of available chambers
        if settings.contains("n_chamber"):
            self.n_chamber = int(settings.value("n_chamber"))
        else:
            self.n_chamber = 1
            settings.setValue("n_chamber", self.n_chamber)

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

    def start_workstation(self):
        # Load information from settings or set defaults
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        settings = QSettings(desktop + "/py-behav/pybehave.ini", QSettings.IniFormat)
        # Store information on the available sources
        # for (_, module_name, _) in iter_modules([package_dir]):
        #     # import the module and iterate through its attributes
        #     module = importlib.import_module(f"Sources.{module_name}")
        #     for attribute_name in dir(module):
        #         attribute = getattr(module, attribute_name)
        #         if isclass(attribute):
        #             # Add the class to this package's variables
        #             globals()[attribute_name] = attribute
        if settings.contains("sources"):
            self.sources = eval(settings.value("sources"))
            for name, code in self.sources.items():
                segs = code.split('(', 1)
                source_type = getattr(importlib.import_module("Sources." + segs[0]), segs[0])
                self.sources[name] = source_type(*eval("(" + segs[1]))
                self.sources[name].sid = name
        else:
            settings.setValue("sources", '{}')
        source_connections = {}
        for name, source in self.sources.items():
            tpq, sourceq = multiprocessing.Pipe()
            source.queue = sourceq
            source_connections[name] = tpq
            source.start()

        app = QApplication(sys.argv)
        self.wsg = WorkstationGUI(self)
        self.gui_queue, gui_out = multiprocessing.Pipe(False)
        self.qui_events_queue, gui_events_out = multiprocessing.Pipe(False)
        self.mainq, tpq = multiprocessing.Pipe()
        self.tp = TaskProcess(tpq, gui_out, source_connections)
        self.tp.start()
        self.gui_task = threading.Thread(target=self.update_gui)
        self.gui_task.start()
        self.gui_event_task = threading.Thread(target=self.gui_event_loop, args=[gui_events_out])
        self.gui_event_task.start()

        # atexit.register(lambda: self.exit_handler())
        # signal.signal(signal.SIGTERM, self.exit_handler)
        # signal.signal(signal.SIGINT, self.exit_handler)
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

    def main(self):
        while True:
            event = self.decoder.decode(self.mainq.recv_bytes())
            if isinstance(event, PybEvents.StopEvent):
                self.wsg.chambers[event.chamber].stop(from_click=False)
            elif isinstance(event, PybEvents.ErrorEvent):
                if "chamber" in event.metadata:
                    self.ed = QMessageBox()
                    self.ed.setIcon(QMessageBox.Critical)
                    self.ed.setWindowTitle("Error adding task")
                    if event.error == "ComponentRegisterError":
                        self.ed.setText("A Component failed to register\n" + event.traceback)
                    elif event.error == "SourceUnavailableError":
                        self.ed.setText("A requested Source is currently unavailable")
                    elif event.error == "MalformedProtocolError":
                        self.ed.setText("Error raised when parsing Protocol file\n" + event.traceback)
                    elif event.error == "MalformedAddressFileError":
                        self.ed.setText("Error raised when parsing AddressFile\n" + event.traceback)
                    elif event.error == "InvalidComponentTypeError":
                        self.ed.setText("A Component in the AddressFile is an invalid type")
                    elif "sid" in event.metadata:
                        self.ed.setText("Unhandled exception in source '" + event.metadata["sid"] + "'\n" + event.traceback)
                    else:
                        self.ed.setText("Unhandled exception\n" + event.traceback)
                    self.ed.setStandardButtons(QMessageBox.Ok)
                    self.ed.show()
                    self.wsg.remove_task(event.metadata["chamber"])
            elif isinstance(event, PybEvents.UnavailableSourceEvent):
                self.sources[event.sid].available = False
                if self.wsg.sd is not None and self.wsg.sd.isVisible():
                    self.wsg.sd.update_source_availability()

    def add_task(self, chamber: int, task_name: str, subject_name: str, address_file: str, protocol: str, task_event_loggers: str) -> None:
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
        self.mainq.send_bytes(self.encoder.encode(PybEvents.AddTaskEvent(chamber, task_name, task_event_loggers, metadata=metadata)))

    async def switch_task(self, task_base: Task, task_name: Type[Task], protocol: str = None) -> Task:
        """
        Switch the active Task in a sequence.
        Parameters
        ----------
        task_base : Task
            The base Task of the sequence
        task_name : Class
            The next Task in the sequence
        protocol : dict
            Dictionary representing the protocol for the new Task
        """
        # Create the new Task as part of a sequence
        new_task = task_name()
        new_task.initialize(task_base, task_base.components, protocol)
        gui = getattr(importlib.import_module("Local.GUIs." + task_name.__name__ + "GUI"), task_name.__name__ + "GUI")
        # Position the GUI in pygame
        col = task_base.metadata['chamber'] % self.n_col
        row = math.floor(task_base.metadata['chamber'] / self.n_col)
        # Create the GUI
        self.guis[task_base.metadata['chamber']].sub_gui = gui(
            self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h),
            new_task)
        return new_task

    def remove_task(self, chamber: int, del_loggers: bool = True) -> None:
        """
        Remove the Task from the specified chamber.

        Parameters
        ----------
        del_loggers
        chamber : int
            The chamber from which a Task should be removed
        """
        self.mainq.send_bytes(self.encoder.encode(PybEvents.ClearEvent(chamber, del_loggers)))

    def gui_event_loop(self, out: Connection) -> None:
        while True:
            event = pygame.event.wait()
            out.send_bytes(self.encoder.encode([PybEvents.PygameEvent(event.type, event.__dict__)]))

    def update_gui(self) -> None:
        conns = [self.qui_events_queue, self.gui_queue]
        while True:
            for ready in multiprocessing.connection.wait(conns):
                events = self.decoder.decode(ready.recv_bytes())
                for event in events:
                    if isinstance(event, PybEvents.AddTaskEvent):
                        gui = getattr(importlib.import_module("Local.GUIs." + event.task_name + "GUI"), event.task_name + "GUI")
                        # Position the GUI in pygame
                        col = event.chamber % self.n_col
                        row = math.floor(event.chamber / self.n_col)
                        # Create the GUI
                        self.guis[event.chamber] = gui(event, self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h), self)
                    elif isinstance(event, PybEvents.TaskEvent):
                        if event.chamber in self.guis:
                            for widget in self.wsg.chambers[event.chamber].widgets:
                                if isinstance(widget, EventWidget):
                                    widget.handle_event(event)
                            self.guis[event.chamber].handle_event(event)
                            col = event.chamber % self.n_col
                            row = math.floor(event.chamber / self.n_col)
                            rect = pygame.Rect((col * self.w, row * self.h, self.w, self.h))
                            if isinstance(event, PybEvents.InitEvent) or isinstance(event, PybEvents.StartEvent):
                                self.guis[event.chamber].complete = False
                                self.guis[event.chamber].draw()
                                self.gui_updates.append(rect)
                            elif isinstance(event, PybEvents.TaskCompleteEvent):
                                self.guis[event.chamber].complete = True
                                self.guis[event.chamber].draw()
                                self.gui_updates.append(rect)
                                self.wsg.chambers[event.chamber - 1].stop(False)
                            elif isinstance(event, PybEvents.ClearEvent) and event.del_loggers:
                                pygame.draw.rect(self.task_gui, Colors.black, rect)
                                self.gui_updates.append(rect)
                                self.wsg.remove_task(event.chamber + 1)
                                del self.guis[event.chamber]
                            else:
                                if isinstance(self.guis[event.chamber], SequenceGUI):
                                    elements = self.guis[event.chamber].get_all_elements()
                                else:
                                    elements = self.guis[event.chamber].elements
                                for element in elements:
                                    if element.has_updated():
                                        element.draw()
                                        self.gui_updates.append(element.rect.move(col * self.w, row * self.h))
                    elif isinstance(event, PybEvents.HeartbeatEvent) or isinstance(event, PybEvents.PygameEvent):
                        for key in self.guis.keys():
                            self.guis[key].handle_event(event)
                            col = key % self.n_col
                            row = math.floor(key / self.n_col)
                            if isinstance(self.guis[key], SequenceGUI):
                                elements = self.guis[key].get_all_elements()
                            else:
                                elements = self.guis[key].elements
                            for element in elements:
                                if element.has_updated():
                                    element.draw()
                                    self.gui_updates.append(element.rect.move(col * self.w, row * self.h))
                    if time.perf_counter() - self.last_frame > 1 / self.fr:
                        if len(self.gui_updates) > 0:
                            pygame.display.update(self.gui_updates)
                            self.gui_updates = []
                        self.last_frame = time.perf_counter()
