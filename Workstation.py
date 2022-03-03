import importlib
import threading

from GUIs import *
import pygame


class Workstation:

    def __init__(self):
        self.tasks = {}
        self.event_loggers = {}
        self.task_gui = pygame.display.set_mode((500, 990), pygame.RESIZABLE, 32)
        self.guis = {}
        pygame.init()

    def add_task(self, chamber, task_name, sources, address_file, protocol, task_event_loggers):
        task_module = importlib.import_module("Tasks."+task_name)
        task = getattr(task_module, task_name)
        self.tasks[chamber] = task(self, sources, address_file, protocol)
        self.event_loggers[chamber] = task_event_loggers
        gui = getattr(importlib.import_module("GUIs." + task_name + "GUI"), task_name + "GUI")
        self.guis[chamber] = gui(self, self.tasks[chamber])

    def remove_task(self, chamber):
        self.tasks[chamber].stop()
        self.event_loggers[chamber].close()
        del self.tasks[chamber]
        del self.event_loggers[chamber]

    # Should this be parallelized?
    def loop(self):
        for key in self.tasks:
            events = self.tasks[key].main_loop()
            self.event_loggers[key].log_events(events)
            self.guis[key].handle_events()
            self.guis[key].draw()
        pygame.display.flip()
