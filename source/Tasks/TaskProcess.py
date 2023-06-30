import importlib
import queue
import re
from multiprocessing import Process, Queue
from typing import Dict, Tuple

from Events import PybEvents
from Events.LoggerEvent import LoggerEvent
from Utilities.PipeQueue import PipeQueue


class TaskProcess(Process):

    def __init__(self, inq: Queue, outq: PipeQueue, sourceq: Dict[str, Tuple[PipeQueue, PipeQueue]]):
        super().__init__()
        self.inq = inq
        self.outq = outq
        self.soureq = sourceq
        self.tasks = {}
        self.task_event_loggers = {}

    def run(self):
        while True:
            try :
                event = self.inq.get(timeout=0.1)
                if isinstance(event, PybEvents.AddTaskEvent):
                    metadata = {"chamber": event.chamber, "subject": event.subject_name, "protocol": event.protocol,
                                "address_file": event.address_file}
                    try:
                        task_module = importlib.import_module("Local.Tasks." + event.task_name)
                        task = getattr(task_module, event.task_name)
                        self.tasks[event.chamber] = task()
                        self.tasks[event.chamber].initialize(self, metadata, self.sources)  # Create the task

                        self.task_event_loggers[event.chamber] = []
                        types = list(
                            map(lambda x: x.split("))")[-1], event.task_event_loggers[1].split("((")))  # Get the type of each logger
                        params = list(
                            map(lambda x: x.split("((")[-1], event.task_event_loggers[1].split("))")))  # Get the parameters for each logger
                        for i in range(len(types) - 1):
                            logger_type = getattr(importlib.import_module("Events." + types[i]),
                                                  types[i])  # Import the logger
                            param_vals = re.findall("\|\|(.+?)\|\|", params[i])  # Extract the parameters
                            self.task_event_loggers[event.chamber].append(logger_type(*param_vals))  # Instantiate the logger

                        for logger in self.task_event_loggers[event.chamber]:
                            logger.set_task(self.tasks[event.chamber])
                        self.inq.put(PybEvents.InitEvent(event.chamber))
                    except BaseException as e:
                        print(type(e).__name__)
                        self.outq.put(PybEvents.ErrorEvent(e))
                elif isinstance(event, PybEvents.ExitEvent):
                    return
                elif isinstance(event, PybEvents.TaskEvent):
                    task = self.tasks[event.chamber]
                    if isinstance(event, PybEvents.StartEvent):
                        # TASK SEQUENCE FUNCTIONALITY IS BROKEN
                        if task is self.tasks[task.metadata["chamber"]]:
                            for el in self.task_event_loggers[task.metadata["chamber"]]:  # Start all EventLoggers
                                el.start_()
                        task.start__()
                        new_event = PybEvents.StateEnterEvent(task.metadata["chamber"], task.state, event.metadata)
                        self.tasks[task.metadata["chamber"]].main_loop(new_event)
                        self.log_event(new_event.format(task))
                    elif isinstance(event, PybEvents.TaskCompleteEvent):
                        if task is not self.tasks[task.metadata["chamber"]]:  # if it's a child task
                            task.stop__()
                            self.tasks[task.metadata["chamber"]].main_loop(event)
                        else:
                            self.wsg.chambers[task.metadata["chamber"]].stop()
                            task.complete = True
                    elif isinstance(event, PybEvents.StopEvent):
                        new_event = PybEvents.StateExitEvent(task, task.state, event.metadata)
                        self.tasks[task.metadata["chamber"]].main_loop(event)
                        self.log_event(new_event.format(task))
                        task.stop__()
                        self.log_event(event.format(task))
                    elif isinstance(event, PybEvents.PauseEvent):
                        task.pause__()
                        self.tasks[task.metadata["chamber"]].main_loop(event)
                        self.log_event(event.format(task))
                    elif isinstance(event, PybEvents.ResumeEvent):
                        task.resume__()
                        self.tasks[task.metadata["chamber"]].main_loop(event)
                    elif isinstance(event, PybEvents.InitEvent):
                        task.init()
                    elif isinstance(event, PybEvents.ClearEvent):
                        task.clear()
                        del_loggers = event.del_loggers
                        if del_loggers:
                            for logger in self.task_event_loggers[task.metadata["chamber"]]:
                                logger.close_()
                            del self.task_event_loggers[task.metadata["chamber"]]
                        for comp in self.tasks[task.metadata["chamber"]].components.values():
                            comp[0].close()
                        del self.tasks[task.metadata["chamber"]]
                        event.done.set()
                    elif isinstance(event, PybEvents.ComponentUpdateEvent):
                        comp = task.components[event.comp_id][0]
                        if comp.update(event.value) and task.started and not task.paused:
                            if event.metadata is None:
                                event.metadata = {}
                            event.metadata["value"] = comp.state
                            new_event = PybEvents.ComponentChangedEvent(task, comp, event.metadata)
                            self.tasks[task.metadata["chamber"]].main_loop(new_event)
                            self.log_event(new_event.format(task))
                            if task.is_complete_():
                                self.inq.put(PybEvents.TaskCompleteEvent(task.metadata["chamber"]))
                    elif isinstance(event, PybEvents.StatefulEvent):
                        if task.started and not task.paused:
                            self.tasks[task.metadata["chamber"]].main_loop(event)
                            if task.is_complete_():
                                self.inq.put(PybEvents.TaskCompleteEvent(task))
                    if isinstance(event, PybEvents.Loggable):
                        if task.started and not task.paused:
                            self.log_event(event.format(task))
            except queue.Empty:
                event = PybEvents.HeartbeatEvent()
                for key in self.tasks.keys():
                    if self.tasks[key].started and not self.tasks[key].paused:
                        self.tasks[key].main_loop(event)

    def log_event(self, event: LoggerEvent):
        for logger in self.task_event_loggers[event.event.chamber]:
            logger.queue.put_nowait(event)
