import importlib
import math
from queue import Queue, Empty
from threading import Thread
from typing import List

from Events.EventLogger import EventLogger


class TaskThread(Thread):
    def __init__(self, chamber: int, task_name: str, subject_name: str, address_file: str, protocol: str,
                 task_event_loggers: List[EventLogger], queue: Queue):
        super().__init__()
        self.queue = queue
        task_module = importlib.import_module("Local.Tasks." + task_name)
        task = getattr(task_module, task_name)
        self.metadata = {"chamber": chamber, "subject": subject_name, "protocol": protocol,
                         "address_file": address_file}
        self.task = task(self, self.metadata, self.sources, address_file, protocol)  # Create the task
        self.task_event_loggers = task_event_loggers
        for logger in task_event_loggers:
            logger.set_task(self.task)
        gui = getattr(importlib.import_module("Local.GUIs." + task_name + "GUI"), task_name + "GUI")
        # Position the GUI in pygame
        col = chamber % self.n_col
        row = math.floor(chamber / self.n_col)
        self.gui = gui(self.task_gui.subsurface(col * self.w, row * self.h, self.w, self.h), self.task)
        self.timeout = None

    def run(self):
        while True:
            try:
                event = self.queue.get(timeout=self.timeout)
                if isinstance(event, self.StartEvent):
                    self.task.start__()
                elif isinstance(event, self.StopEvent):
                    self.task.stop__()
                elif isinstance(event, self.PauseEvent):
                    self.task.pause__()
                elif isinstance(event, self.ResumeEvent):
                    self.task.resume__()
                elif isinstance(event, self.ClearEvent):
                    self.task.clear()
                elif isinstance(event, self.ComponentChangeEvent):
                    self.task.main_loop(self.task.components[event.comp_id])
                elif isinstance(event, self.TimeoutEvent):
                    self.timeout = event.timeout
            except Empty:
                self.task.main_loop()

    class StartEvent:
        pass

    class StopEvent:
        pass

    class PauseEvent:
        pass

    class ResumeEvent:
        pass

    class ClearEvent:
        pass

    class ComponentChangeEvent:
        def __init__(self, comp_id):
            self.comp_id = comp_id

    class TimeoutEvent:
        def __init__(self, timeout):
            self.timeout = timeout
