from __future__ import annotations

import multiprocessing
import sys
import threading
import time
import traceback
from multiprocessing.dummy.connection import Connection
from typing import List

import msgspec

from pybehave.Events import PybEvents
from pybehave.Events.EventWidget import EventWidget
from pybehave.GUIs.SequenceGUI import SequenceGUI
from pybehave.Tasks.TaskProcess import TaskProcess
from pybehave.Workstation.WorkstationGUI import WorkstationGUI

import importlib

import math

from pybehave.GUIs import Colors
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
        self.gui_stop_event = None
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
        sys.path.insert(0, f'{desktop}/py-behav/')
        if settings.contains("sources"):
            self.sources = eval(settings.value("sources"))
            for name, code in self.sources.items():
                segs = code.split('(', 1)
                try:
                    source_type = getattr(importlib.import_module("pybehave.Sources." + segs[0]), segs[0])
                except ModuleNotFoundError:
                    source_type = getattr(importlib.import_module("Local.Sources." + segs[0]), segs[0])
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
        self.gui_stop_event = threading.Event()
        self.gui_event_task = threading.Thread(target=self.gui_event_loop, args=[gui_events_out, self.gui_stop_event])
        self.gui_event_task.start()

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

    def add_task(self, chamber: int, task_name: str, subject_name: str, address_file: str, protocol: str, task_event_loggers: str) -> None:
        """
        Creates a Task and adds it to the chamber.

        Parameters
        ----------
        chamber : int
            The index of the chamber where the task will be added
        task_name : string
            The name corresponding to the Task class
        subject_name : string
            The name of the subject completing this Task
        address_file : string
            The file path for the Address File
        protocol : string
            The file path for the Protocol
        task_event_loggers : list
            The list of EventLoggers for the task
        """
        metadata = {"chamber": chamber, "subject": subject_name, "protocol": protocol, "address_file": address_file}
        self.mainq.send_bytes(self.encoder.encode(PybEvents.AddTaskEvent(chamber, task_name, task_event_loggers, metadata=metadata)))

    def remove_task(self, chamber: int, del_loggers: bool = True) -> None:
        """
        Remove the Task from the specified chamber.

        Parameters
        ----------
        chamber : int
            The chamber from which a Task should be removed
        del_loggers : bool
            Indicates if the event loggers should be cleared along with the chamber
        """
        self.mainq.send_bytes(self.encoder.encode(PybEvents.ClearEvent(chamber, del_loggers)))

    def gui_event_loop(self, out: Connection, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            event = pygame.event.wait(100)  # millisecond timeout
            if event.type != pygame.NOEVENT:
                out.send_bytes(self.encoder.encode([PybEvents.PygameEvent(event.type, event.__dict__)]))

    def update_gui(self) -> None:
        conns = [self.qui_events_queue, self.gui_queue]
        while True:
            for ready in multiprocessing.connection.wait(conns):
                events = self.decoder.decode(ready.recv_bytes())
                for event in events:
                    try:
                        if isinstance(event, PybEvents.AddTaskEvent):
                            module = importlib.import_module("Local.GUIs." + event.task_name + "GUI")
                            module = importlib.reload(module)
                            gui = getattr(module, event.task_name + "GUI")
                            # Position the GUI in pygame
                            col = event.chamber % self.n_col
                            row = math.floor(event.chamber / self.n_col)
                            # Create the GUI
                            self.guis[event.chamber] = gui(event, self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h), self)
                        elif isinstance(event, PybEvents.TaskEvent):
                            if event.chamber in self.guis:
                                for widget in self.wsg.chambers[event.chamber].widgets:
                                    if isinstance(widget, EventWidget):
                                        widget.emitter.emit(event)
                                self.guis[event.chamber].handle_event(event)
                                col = event.chamber % self.n_col
                                row = math.floor(event.chamber / self.n_col)
                                rect = pygame.Rect((col * self.w, row * self.h, self.w, self.h))
                                if isinstance(event, PybEvents.InitEvent) or isinstance(event, PybEvents.StartEvent):
                                    if "sub_task" in event.metadata:
                                        self.guis[event.chamber].switch_sub_gui(event)
                                    self.guis[event.chamber].complete = False
                                    self.guis[event.chamber].draw()
                                    self.gui_updates.append(rect)
                                elif isinstance(event, PybEvents.OutputFileChangedEvent):
                                    self.guis[event.chamber].subject_name.text = event.subject
                                    self.guis[event.chamber].draw()
                                    self.gui_updates.append(rect)
                                elif isinstance(event, PybEvents.TaskCompleteEvent):
                                    if not isinstance(self.guis[event.chamber], SequenceGUI) or "sequence_complete" in event.metadata:
                                        self.guis[event.chamber].complete = True
                                        self.guis[event.chamber].draw()
                                        self.gui_updates.append(rect)
                                        self.wsg.chambers[event.chamber].stop(False)
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
                        elif isinstance(event, PybEvents.ErrorEvent):
                            self.handle_error(event)
                        elif isinstance(event, PybEvents.UnavailableSourceEvent):
                            self.sources[event.sid].available = False
                            if self.wsg.sd is not None and self.wsg.sd.isVisible():
                                self.wsg.sd.update_source_availability()
                        elif isinstance(event, PybEvents.ExitEvent):
                            return

                        if time.perf_counter() - self.last_frame > 1 / self.fr:
                            if len(self.gui_updates) > 0:
                                pygame.display.update(self.gui_updates)
                                self.gui_updates = []
                            self.last_frame = time.perf_counter()
                    except BaseException as e:
                        metadata = {"chamber": event.chamber} if isinstance(event, PybEvents.TaskEvent) else {}
                        tb = traceback.format_exc()
                        self.handle_error(PybEvents.ErrorEvent(type(e).__name__, tb, metadata=metadata))

    def handle_error(self, event: PybEvents.ErrorEvent):
        print(event.traceback)
        if 'chamber' in event.metadata:
            chamber = event.metadata['chamber']
            chamber_suffix = "in chamber " + str(chamber + 1) + "<br>"
            if event.error == "ComponentRegisterError":
                error_message = "A Component failed to register " + chamber_suffix + event.traceback
                self.fatal_chamber_exception(chamber)
            elif event.error == "SourceUnavailableError":
                error_message = "A requested Source is currently unavailable following an operation in " + chamber_suffix + event.traceback
                self.fatal_chamber_exception(chamber)
            elif event.error == "MalformedProtocolError":
                error_message = "Error raised when parsing Protocol file " + chamber_suffix + event.traceback
                self.fatal_chamber_exception(chamber)
            elif event.error == "MalformedAddressFileError":
                error_message = "Error raised when parsing AddressFile " + chamber_suffix + event.traceback
                self.fatal_chamber_exception(chamber)
            elif event.error == "InvalidComponentTypeError":
                error_message = "A Component in the AddressFile is an invalid type " + chamber_suffix + event.traceback
                self.fatal_chamber_exception(chamber)
            elif "sid" in event.metadata:
                error_message = "Unhandled exception in source '" + event.metadata["sid"] + "'\n" + event.traceback
            else:
                error_message = "Unhandled exception " + chamber_suffix + event.traceback
        else:
            error_message = f"Unhandled exception in pybehave processing code. <a href='https://github.com/tne-lab/py-behav-box-v2/issues/new?title=Unhandled%20Exception&body={event.traceback}'>Click here</a> to create a GitHub issue<br>" + event.traceback
        self.wsg.error.emit(error_message)

    def fatal_chamber_exception(self, chamber):
        col = chamber % self.n_col
        row = math.floor(chamber / self.n_col)
        rect = pygame.Rect((col * self.w, row * self.h, self.w, self.h))
        self.guis[chamber].dead = True
        self.guis[chamber].draw()
        self.gui_updates.append(rect)
        self.wsg.chambers[chamber].fatal_exception()

    def exit(self, stop_tasks=False):
        """
            Callback for when PyBehave is closed.
            - Sends an Exit event to the main q and joins the TaskProcess.
            - The TP tells all sources to close, and the source processes are joined here.
            - Joins the update_gui and gui_event_loop threads.
            - Quits pygame.
        """
        if stop_tasks:
            for chamber, gui in self.guis.items():
                if gui.started and not gui.paused:
                    self.mainq.send_bytes(self.encoder.encode(PybEvents.StopEvent(chamber)))

        self.mainq.send_bytes(self.encoder.encode(PybEvents.ExitEvent()))
        self.tp.join()

        # Join source processes. Assumes all source have terminated
        for source in self.sources.values():
            source.join()

        self.gui_stop_event.set()

        # Join event threads
        self.gui_event_task.join()
        self.gui_task.join()

        pygame.quit()
