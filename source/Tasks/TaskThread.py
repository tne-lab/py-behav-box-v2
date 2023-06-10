from __future__ import annotations
import importlib
import math
import threading
import time
from queue import Queue
from threading import Thread
from typing import List, Dict, Type, TYPE_CHECKING

import pygame

from Events.LoggerEvent import LoggerEvent
from Tasks import TaskEvents

if TYPE_CHECKING:
    from Events.EventLogger import EventLogger
    from Tasks.Task import Task
    from Workstation.Workstation import Workstation


class TaskThread(Thread):
    def __init__(self, ws: Workstation, task_name: str, metadata: Dict, queue: Queue, task_event_loggers: List[EventLogger]):
        super().__init__()
        self.queue = queue
        self.ws = ws
        task_module = importlib.import_module("Local.Tasks." + task_name)
        task = getattr(task_module, task_name)
        self.metadata = metadata
        self.task = task(self, self.metadata, ws.sources)  # Create the task
        self.event_loggers = task_event_loggers
        for logger in task_event_loggers:
            logger.set_task(self.task)
        gui = getattr(importlib.import_module("Local.GUIs." + task_name + "GUI"), task_name + "GUI")
        # Position the GUI in pygame
        self.gui = gui(pygame.Surface((ws.w, ws.h)), self.task)
        self.timeout = None
        self.stopping = False
        self.event_disconnect = threading.Event()
        self.gui_disconnect = threading.Event()
        self.gui_events_disconnect = threading.Event()
        ws.gui_notifier.set()

    def run(self):
        del_loggers = False
        while not self.stopping:
            event = self.queue.get()
            if isinstance(event, TaskEvents.StartEvent):
                for el in self.event_loggers:  # Start all EventLoggers
                    el.start()
                self.task.start__()
                new_event = TaskEvents.StateEnterEvent(self.task.state, event.metadata)
                self.task.main_loop(new_event)
                self.log_event(LoggerEvent(new_event, new_event.state.name, new_event.state.value, self.task.time_elapsed()))
            elif isinstance(event, TaskEvents.TaskCompleteEvent):
                self.ws.wsg.chambers[self.metadata["chamber"]].stop()
                self.task.complete = True
            elif isinstance(event, TaskEvents.StopEvent):
                new_event = TaskEvents.StateExitEvent(self.task.state, event.metadata)
                self.task.main_loop(new_event)
                self.log_event(LoggerEvent(new_event, new_event.state.name, new_event.state.value, self.task.time_elapsed()))
                self.task.stop__()
            elif isinstance(event, TaskEvents.PauseEvent):
                self.task.pause__()
                self.task.main_loop(event)
                self.log_event(LoggerEvent(event, self.task.state.name, self.task.state.name.value, self.task.time_elapsed()))
            elif isinstance(event, TaskEvents.ResumeEvent):
                self.task.resume__()
                self.task.main_loop(event)
                self.log_event(LoggerEvent(event, self.task.state.name, self.task.state.name.value, self.task.time_elapsed()))
            elif isinstance(event, TaskEvents.ClearEvent):
                self.task.clear()
                self.stopping = True
                del_loggers = event.del_loggers
            elif isinstance(event, TaskEvents.StateEnterEvent):
                self.task.main_loop(event)
                self.log_event(LoggerEvent(event, event.state.name, event.state.value, self.task.time_elapsed()))
            elif isinstance(event, TaskEvents.StateExitEvent):
                self.task.main_loop(event)
                self.log_event(LoggerEvent(event, event.state.name, event.state.value, self.task.time_elapsed()))
            elif isinstance(event, TaskEvents.ComponentUpdateEvent):
                comp = self.task.components[event.comp_id]
                comp.update(event.value)
                if self.task.started:
                    new_event = TaskEvents.ComponentChangedEvent(comp, event.metadata)
                    self.task.main_loop(new_event)
                    if self.task.is_complete_():
                        self.queue.put(TaskEvents.TaskCompleteEvent(), block=False)
                    self.log_event(LoggerEvent(new_event, comp.id, comp.address, self.task.time_elapsed()))
            elif isinstance(event, TaskEvents.GUIEvent):
                if self.task.started:
                    self.task.main_loop(event)
                    if self.task.is_complete_():
                        self.queue.put(TaskEvents.TaskCompleteEvent(), block=False)
                    self.log_event(LoggerEvent(event, event.event.name, event.event.value, self.task.time_elapsed()))
            elif isinstance(event, TaskEvents.TimeoutEvent):  # Should this log an event?
                self.task.main_loop(event)
                if self.task.is_complete_():
                    self.queue.put(TaskEvents.TaskCompleteEvent(), block=False)
            elif isinstance(event, TaskEvents.HeartbeatEvent):
                if self.task.started:
                    self.task.main_loop(event)
            self.ws.gui_notifier.set()

        self.gui_disconnect.wait()
        self.gui_events_disconnect.wait()
        if del_loggers:
            for el in self.event_loggers:  # Close all associated EventLoggers
                el.close_()
        for c in self.task.components.values():
            c.close()

    def switch_task(self, task_name: Type[Task], protocol: str = None) -> Task:
        new_task = task_name(self.task, self.task.components, protocol)
        gui = getattr(importlib.import_module("Local.GUIs." + task_name.__name__ + "GUI"), task_name.__name__ + "GUI")
        # Position the GUI in pygame
        col = self.metadata['chamber'] % self.ws.n_col
        row = math.floor(self.metadata['chamber'] / self.ws.n_col)
        # Create the GUI
        self.gui[self.metadata['chamber']].sub_gui = gui(
            self.ws.task_gui.subsurface(col * self.ws.w, row * self.ws.h, self.ws.w, self.ws.h),
            new_task)
        return new_task

    def log_event(self, event: LoggerEvent):
        for logger in self.event_loggers:
            logger.queue.put(event, block=False)
