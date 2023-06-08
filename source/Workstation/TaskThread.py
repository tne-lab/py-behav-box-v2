from __future__ import annotations
import importlib
import math
import threading
from queue import Queue, Empty
from threading import Thread
from typing import List, Dict, Type, TYPE_CHECKING, Any

from Components.Component import Component

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
        col = metadata["chamber"] % ws.n_col
        row = math.floor(metadata["chamber"] / ws.n_col)
        self.gui = gui(ws.task_gui.subsurface(col * ws.w, row * ws.h, ws.w, ws.h), self.task)
        self.timeout = None
        self.stopping = False
        self.event_disconnect = threading.Event()
        self.gui_disconnect = threading.Event()
        self.gui_events_disconnect = threading.Event()
        ws.gui_notifier.set()

    def run(self):
        del_loggers = False
        while not self.stopping:
            try:
                event = self.queue.get(timeout=self.timeout)
                if isinstance(event, self.StartEvent):
                    for el in self.event_loggers:  # Start all EventLoggers
                        el.start_()
                    self.task.start__()
                elif isinstance(event, self.StopEvent):
                    self.task.stop__()
                elif isinstance(event, self.PauseEvent):
                    self.task.pause__()
                elif isinstance(event, self.ResumeEvent):
                    self.task.resume__()
                elif isinstance(event, self.ClearEvent):
                    self.task.clear()
                    self.stopping = True
                    del_loggers = event.del_loggers
                elif isinstance(event, self.ComponentUpdateEvent):
                    comp = self.task.components[event.comp_id]
                    comp.update(event.value)
                    self.task.main_loop(self.ComponentChangedEvent(comp))
                elif isinstance(event, self.TimeoutEvent):
                    self.timeout = event.timeout
            except Empty:
                self.task.main_loop(self.TimeoutEvent(self.timeout))
            self.ws.gui_notifier.set()
            if len(self.task.events) > 0:
                self.ws.event_notifier.set()

        self.ws.event_notifier.set()
        self.event_disconnect.wait()
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

    class Event:
        pass

    class StartEvent(Event):
        pass

    class StopEvent(Event):
        pass

    class PauseEvent(Event):
        pass

    class ResumeEvent(Event):
        pass

    class ClearEvent(Event):
        def __init__(self, del_loggers):
            self.del_loggers = del_loggers

    class ComponentUpdateEvent(Event):
        def __init__(self, comp_id: str, value: Any):
            self.comp_id = comp_id
            self.value = value

    class ComponentChangedEvent(Event):
        def __init__(self, comp: Component):
            self.comp = comp

    class TimeoutEvent(Event):
        def __init__(self, timeout):
            self.timeout = timeout
