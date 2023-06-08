from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import overload, Any, Type, Dict, List, Tuple

from Components.Component import Component
from Sources.Source import Source
from Tasks.Task import Task
import time

from Workstation.Workstation import Workstation


class TaskSequence(Task):
    __metaclass__ = ABCMeta

    @overload
    def __init__(self, ws: Workstation, metadata: Dict[str, Any], sources: Dict[str, Source], address_file: str = "", protocol: str = ""):
        ...

    @overload
    def __init__(self, task: Task, components: List[Component], protocol: str):
        ...

    def __init__(self, *args):
        super().__init__(*args)
        self.cur_task = None
        self.init_task = None
        self.init_protocol = None
        self.sub_start_time = 0
        self.init_sequence__()

    @staticmethod
    @abstractmethod
    def get_tasks() -> List[Type[Task]]:
        raise NotImplementedError

    @staticmethod
    def get_sequence_components() -> Dict[str, List[Type[Component]]]:
        return {}

    def get_components(self) -> Dict[str, List[Type[Component]]]:
        components = {}
        for task in self.get_tasks():
            sub_components = task.get_components()
            for name in sub_components:
                if name not in components:
                    components[name] = sub_components[name]
                elif len(components[name]) < len(sub_components[name]):
                    components[name] = sub_components[name]
        components.update(self.get_sequence_components())
        return components

    def initialize(self) -> None:
        self.cur_task = self.ws.switch_task(self, self.init_task, self.init_protocol)

    def init_sequence__(self) -> None:
        res = self.init_sequence()
        self.init_task = res[0]
        if len(res) > 1:
            self.init_protocol = res[1]

    @abstractmethod
    def init_sequence(self) -> Tuple[Type[Task], str]:
        raise NotImplementedError

    def switch_task(self, task: Type[Task], seq_state: Enum, protocol: str, metadata: Any = None) -> None:
        self.cur_task.stop()
        self.log_sequence_events()
        self.change_state(seq_state, metadata)
        self.cur_task = self.task_thread.switch_task(task, protocol)
        self.start_sub()

    def log_sequence_events(self) -> None:
        sub_events = self.cur_task.events
        self.cur_task.events = []
        for event in sub_events:
            event.entry_time += self.sub_start_time - self.start_time
        self.events.extend(sub_events)

    def main_loop(self, component) -> None:
        self.cur_time = time.time()
        self.cur_task.cur_time = self.cur_time
        self.cur_task.handle_input()
        self.handle_input(component)
        if hasattr(self.cur_task, self.cur_task.state.name):
            state_method = getattr(self.cur_task, self.cur_task.state.name)
            state_method(component)
        if hasattr(self, self.state.name):
            state_method = getattr(self, self.state.name)
            state_method(component)
        self.log_sequence_events()

    def start_sub(self) -> None:
        self.sub_start_time = self.cur_time
        self.cur_task.start__()

    def start__(self) -> None:
        self.initialize()
        super(TaskSequence, self).start__()
        self.start_sub()
        self.log_sequence_events()

    def pause__(self) -> None:
        self.cur_task.pause__()
        self.log_sequence_events()
        super(TaskSequence, self).pause__()

    def stop__(self) -> None:
        self.cur_task.stop__()
        self.log_sequence_events()
        super(TaskSequence, self).stop__()

    def resume__(self) -> None:
        super(TaskSequence, self).resume__()
        self.cur_task.resume__()
        self.log_sequence_events()
