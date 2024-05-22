import collections
import copy
import importlib
import multiprocessing
import os
import re
import traceback
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from typing import Dict

import msgspec.msgpack
import psutil

from pybehave.Events import PybEvents
from pybehave.Events.FileEventLogger import FileEventLogger
from pybehave.Tasks.TaskSequence import TaskSequence
from pybehave.Tasks.TimeoutManager import TimeoutManager


class TaskProcess(Process):

    def __init__(self, mainq: Connection, guiq: Connection, sourceq: Dict[str, Connection]):
        super().__init__()
        self.mainq = mainq
        self.guiq = guiq
        self.sourceq = sourceq
        self.tasks = {}
        self.task_event_loggers = {}
        self.tm = None
        self.tmq_in = None
        self.tmq_out = None
        self.encoder = None
        self.decoder = None
        self.gui_out = []
        self.tp_q = None
        self.logger_q = None
        self.event_responses = {}
        self.source_buffers = {}
        self.connections = []
        self.should_exit = False

    def run(self):
        p = psutil.Process(os.getpid())
        p.nice(psutil.REALTIME_PRIORITY_CLASS)
        self.tm = TimeoutManager()
        self.tm.start()
        self.tp_q = collections.deque()
        self.logger_q = collections.deque()
        self.tmq_in, self.tmq_out = Pipe(False)
        self.connections = [self.mainq, self.tmq_in, *self.sourceq.values()]
        self.encoder = msgspec.msgpack.Encoder(enc_hook=PybEvents.enc_hook)
        self.decoder = msgspec.msgpack.Decoder(type=PybEvents.subclass_union(PybEvents.PybEvent), dec_hook=PybEvents.dec_hook)

        for source in self.sourceq:
            self.source_buffers[source] = []

        self.event_responses = {PybEvents.AddTaskEvent: self.add_task,
                                PybEvents.AddLoggerEvent: self.add_logger,
                                PybEvents.RemoveLoggerEvent: self.remove_logger,
                                PybEvents.OutputFileChangedEvent: self.output_file_changed,
                                PybEvents.StartEvent: self.start_task,
                                PybEvents.TaskCompleteEvent: self.task_complete,
                                PybEvents.StopEvent: self.stop_task,
                                PybEvents.PauseEvent: self.pause_task,
                                PybEvents.ResumeEvent: self.resume_task,
                                PybEvents.InitEvent: self.init_task,
                                PybEvents.ClearEvent: self.clear_task,
                                PybEvents.ComponentUpdateEvent: self.update_component,
                                PybEvents.UnavailableSourceEvent: self.source_unavailable,
                                PybEvents.AddSourceEvent: self.add_source,
                                PybEvents.RemoveSourceEvent: self.remove_source,
                                PybEvents.ErrorEvent: self.error,
                                PybEvents.ConstantsUpdateEvent: self.update_constants,
                                PybEvents.ConstantRemoveEvent: self.remove_constant,
                                PybEvents.ExitEvent: self.prepare_exit}

        while True:
            try:
                ready = multiprocessing.connection.wait(self.connections, timeout=0.1)
                if len(ready) == 0:
                    event = PybEvents.HeartbeatEvent()
                    for key in self.tasks.keys():
                        if self.tasks[key].started and not self.tasks[key].paused:
                            self.tasks[key].main_loop(event)
                    for source in self.source_buffers:
                        if len(self.source_buffers[source]) > 0:
                            self.sourceq[source].send_bytes(self.encoder.encode(self.source_buffers[source]))
                            self.source_buffers[source] = []
                    self.log_gui_event(event)
                else:
                    for r in ready:
                        event = self.decoder.decode(r.recv_bytes())
                        # t = time.perf_counter()
                        self.handle_event(event)
                        # print(time.perf_counter() - t)
                        while len(self.tp_q) > 0:
                            self.handle_event(self.tp_q.popleft())
                        for source in self.source_buffers:
                            if len(self.source_buffers[source]) > 0:
                                self.sourceq[source].send_bytes(self.encoder.encode(self.source_buffers[source]))
                                self.source_buffers[source] = []
                        if isinstance(event, PybEvents.TaskEvent) and len(self.logger_q) > 0:
                            for logger in self.task_event_loggers[event.chamber].values():
                                logger.log_events(self.logger_q)
                            self.logger_q.clear()
            except BaseException as e:
                metadata = {"chamber": event.chamber} if isinstance(event, PybEvents.TaskEvent) else {}
                self.log_gui_event(PybEvents.ErrorEvent(type(e).__name__, traceback.format_exc(),
                                   metadata=metadata))
            if len(self.gui_out) > 0:
                self.guiq.send_bytes(self.encoder.encode(self.gui_out))
                self.gui_out.clear()

            if self.should_exit:
                self.exit()
                break

    def handle_event(self, event):
        event_type = type(event)
        self.log_gui_event(event)
        if event_type in self.event_responses:
            self.event_responses[type(event)](event)
        elif isinstance(event, PybEvents.StatefulEvent):
            task = self.tasks[event.chamber]
            if task.started and not task.paused:
                self.tasks[task.metadata["chamber"]].main_loop(event)
        if isinstance(event, PybEvents.Loggable):
            task = self.tasks[event.chamber]
            if task.started and not task.paused:
                self.log_event(event)

    def add_task(self, event: PybEvents.AddTaskEvent):
        try:
            task_module = importlib.import_module("Local.Tasks." + event.task_name)
            task_module = importlib.reload(task_module)
            task = getattr(task_module, event.task_name)
            self.tasks[event.chamber] = task()
            self.tasks[event.chamber].initialize(self, event.metadata)  # Create the task

            self.task_event_loggers[event.chamber] = {}
            types = list(
                map(lambda x: x.split("))")[-1],
                    event.task_event_loggers.split("((")))  # Get the type of each logger
            params = list(
                map(lambda x: x.split("((")[-1],
                    event.task_event_loggers.split("))")))  # Get the parameters for each logger
            for i in range(len(types) - 1):
                logger_type = getattr(importlib.import_module("pybehave.Events." + types[i]), types[i])  # Import the logger
                param_vals = re.findall("\|\|(.+?)\|\|", params[i])  # Extract the parameters
                self.task_event_loggers[event.chamber][param_vals[0]] = logger_type(*param_vals)  # Instantiate the logger
            for logger in self.task_event_loggers[event.chamber].values():
                logger.set_task(self.tasks[event.chamber])
            self.tp_q.append(PybEvents.InitEvent(event.chamber))
        except BaseException as e:
            tb = traceback.format_exc()
            print(tb)
            self.mainq.send_bytes(self.encoder.encode(PybEvents.ErrorEvent(type(e).__name__, tb)))

    def add_logger(self, event: PybEvents.AddLoggerEvent):
        segs = event.logger_code.split('((')
        logger_type = getattr(importlib.import_module("pybehave.Events." + segs[0]), segs[0])  # Import the logger
        param_vals = re.findall("\|\|(.+?)\|\|", segs[1].split('))')[0])
        self.task_event_loggers[event.chamber][param_vals[0]] = logger_type(*param_vals)
        self.task_event_loggers[event.chamber][param_vals[0]].set_task(self.tasks[event.chamber])

    def remove_logger(self, event: PybEvents.RemoveLoggerEvent):
        self.task_event_loggers[event.chamber][event.logger_name].close_()
        del self.task_event_loggers[event.chamber][event.logger_name]

    def output_file_changed(self, event: PybEvents.OutputFileChangedEvent):
        self.tasks[event.chamber].metadata["subject"] = event.subject
        for q in self.source_buffers.values():
            q.append(event)
        for el in self.task_event_loggers[event.chamber].values():  # Allow all EventLoggers to handle the change
            if isinstance(el, FileEventLogger):  # Handle the change for FileEventLoggers
                el.output_folder = event.output_file

    def start_task(self, event: PybEvents.StartEvent):
        if "sub_task" in event.metadata:  # If we should start a sub-task
            task = self.tasks[event.chamber].cur_task
        else:
            task = self.tasks[event.chamber]
            if task is self.tasks[task.metadata["chamber"]]:
                for el in self.task_event_loggers[task.metadata["chamber"]].values():  # Start all EventLoggers
                    el.start_()
        metadata = task.start__()
        metadata.update(event.metadata)
        new_event = PybEvents.StateEnterEvent(task.metadata["chamber"], task.state.name, task.state.value,
                                              metadata=metadata)
        self.tasks[task.metadata["chamber"]].main_loop(new_event)
        self.log_event(new_event)
        self.log_gui_event(new_event)

    def task_complete(self, event: PybEvents.TaskCompleteEvent):
        if "sequence_complete" in event.metadata:
            task = self.tasks[event.chamber].cur_task
            task.stop__()
            self.tasks[event.chamber].cur_task = None
        elif isinstance(self.tasks[event.chamber], TaskSequence):
            self.tasks[event.chamber].main_loop(event)
        else:
            task = self.tasks[event.chamber]
            e = PybEvents.StopEvent(event.chamber)
            self.mainq.send_bytes(self.encoder.encode(e))
            self.tp_q.append(e)
            task.complete = True

    def stop_task(self, event: PybEvents.StopEvent):
        task = self.tasks[event.chamber]
        new_event = PybEvents.StateExitEvent(event.chamber, task.state.name, task.state.value, metadata=event.metadata)
        self.tasks[task.metadata["chamber"]].main_loop(event)
        self.log_event(new_event)
        for logger in self.task_event_loggers[event.chamber].values():
            logger.log_events(self.logger_q)
        task.stop__()
        for logger in self.task_event_loggers[event.chamber].values():
            logger.stop()
        self.logger_q.clear()

    def pause_task(self, event: PybEvents.PauseEvent):
        task = self.tasks[event.chamber]
        task.pause__()
        self.tasks[task.metadata["chamber"]].main_loop(event)
        self.log_event(event)

    def resume_task(self, event: PybEvents.ResumeEvent):
        task = self.tasks[event.chamber]
        task.resume__()
        self.tasks[task.metadata["chamber"]].main_loop(event)

    def init_task(self, event: PybEvents.InitEvent):
        self.tasks[event.chamber].init()

    def clear_task(self, event: PybEvents.ClearEvent):
        task = self.tasks[event.chamber]
        task.clear()
        del_loggers = event.del_loggers
        if del_loggers:
            for logger in self.task_event_loggers[task.metadata["chamber"]].values():
                logger.close_()
            del self.task_event_loggers[task.metadata["chamber"]]
        for comp in self.tasks[task.metadata["chamber"]].components.values():
            comp[0].close()
        del self.tasks[task.metadata["chamber"]]

    def update_component(self, event: PybEvents.ComponentUpdateEvent):
        task = self.tasks[event.chamber]
        comp = task.components[event.comp_id][0]
        if comp.update(event.value) and task.started and not task.paused:
            # event.value = comp.state
            metadata = event.metadata.copy()
            metadata["value"] = comp.state
            new_event = PybEvents.ComponentChangedEvent(task.metadata["chamber"], comp, task.components[comp.id][1],
                                                        metadata=metadata)
            self.tasks[task.metadata["chamber"]].main_loop(new_event)
            self.log_event(new_event)

    def update_constants(self, event: PybEvents.ConstantsUpdateEvent):
        for q in self.source_buffers.values():
            q.append(event)
        task = self.tasks[event.chamber]
        for key in event.constants:
            try:
                value = eval(event.constants[key])
                if key not in task.initial_constants:
                    task.initial_constants[key] = copy.deepcopy(task.__getattribute__(key))
                if value != task.__getattribute__(key) and task.started:
                    new_event = PybEvents.ConstantUpdateEvent(task.metadata["chamber"], key, value)
                    self.tp_q.append(new_event)
                task.__setattr__(key, value)
            except:
                pass

    def remove_constant(self, event: PybEvents.ConstantRemoveEvent):
        task = self.tasks[event.chamber]
        if event.constant in task.initial_constants:
            if task.initial_constants[event.constant] != task.__getattribute__(event.constant) and task.started:
                new_event = PybEvents.ConstantUpdateEvent(task.metadata["chamber"], event.constant, task.initial_constants[event.constant])
                self.tp_q.append(new_event)
            task.__setattr__(event.constant, task.initial_constants[event.constant])
            del task.initial_constants[event.constant]

    def log_gui_event(self, event: PybEvents.PybEvent):
        if isinstance(event, PybEvents.TimedEvent) and event.timestamp is None:
            event.acknowledge(self.tasks[event.chamber].time_elapsed())
        self.gui_out.append(event)

    def log_event(self, event: PybEvents.Loggable):
        if isinstance(event, PybEvents.TimedEvent) and event.timestamp is None:
            event.acknowledge(self.tasks[event.chamber].time_elapsed())
        self.logger_q.append(event.format())

    def source_unavailable(self, event: PybEvents.UnavailableSourceEvent):
        self.mainq.send_bytes(self.encoder.encode(event))

    def add_source(self, event: PybEvents.AddSourceEvent):
        self.sourceq[event.sid] = event.conn
        self.source_buffers[event.sid] = []
        self.connections = [self.mainq, self.tmq_in, *self.sourceq.values()]

    def remove_source(self, event: PybEvents.RemoveSourceEvent):
        self.sourceq[event.sid].send_bytes(self.encoder.encode([event]))
        del self.sourceq[event.sid]
        del self.source_buffers[event.sid]
        self.connections = [self.mainq, self.tmq_in, *self.sourceq.values()]

    def error(self, event: PybEvents.ErrorEvent):
        if "sid" in event.metadata and event.metadata["sid"] in self.sourceq:
            del self.sourceq[event.metadata["sid"]]
            del self.source_buffers[event.metadata["sid"]]
        self.mainq.send_bytes(self.encoder.encode(event))

    def prepare_exit(self, event: PybEvents.ExitEvent):
        self.should_exit = True

    def exit(self, *args):
        for q in self.sourceq.values():
            q.send_bytes(self.encoder.encode([PybEvents.CloseSourceEvent()]))
        self.tm.quit()
        self.tm.join()
