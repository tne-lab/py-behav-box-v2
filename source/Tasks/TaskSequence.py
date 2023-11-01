from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Type, Dict, List

from Components.Component import Component
from Events import PybEvents
from Tasks.Task import Task


class TaskSequence(Task):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(TaskSequence, self).__init__()
        self.cur_task = None

    @staticmethod
    @abstractmethod
    def get_tasks() -> List[Type[Task]]:
        raise NotImplementedError

    @staticmethod
    def get_sequence_components() -> Dict[str, List[Type[Component]]]:
        return {}
    
    @staticmethod
    def get_constants() -> Dict[str, Any]:
        return {}

    @classmethod
    def get_components(cls) -> Dict[str, List[Type[Component]]]:
        components = {}
        for task in cls.get_tasks():
            sub_components = task.get_components()
            for name in sub_components:
                if name not in components:
                    components[name] = sub_components[name]
        components.update(cls.get_sequence_components())
        return components

    def switch_task(self, task: Type[Task], seq_state: Enum, protocol: str, metadata: Any = None) -> None:
        if self.cur_task is not None:
            self.cur_task.stop__()
        self.cur_task = task()
        self.cur_task.initialize(self, self.components, protocol)
        metadata = metadata.copy()
        metadata["protocol"] = protocol
        metadata["sub_task"] = str(task)

        if self.state != seq_state:
            self.change_state(seq_state, metadata)
        self.log_event(PybEvents.StartEvent(self.metadata["chamber"], metadata=metadata))

    def main_loop(self, event: PybEvents.PybEvent) -> None:
        if isinstance(event, PybEvents.StateEnterEvent):
            if event.name in self.state_methods:
                self.state = self.States(event.value)
            else:
                self.cur_task.state = self.cur_task.States(event.value)
        elif isinstance(event, PybEvents.StateExitEvent):
            if event.name in self.state_methods and self.state in self.state_timeouts:
                for tm in self.state_timeouts[self.state].values():
                    if tm[1]:
                        self.cancel_timeout(tm[0].name)
            elif event.name in self.cur_task.state_methods and self.state in self.cur_task.state_timeouts:
                for tm in self.cur_task.state_timeouts[self.state].values():
                    if tm[1]:
                        self.cur_task.cancel_timeout(tm[0].name)
        elif isinstance(event, PybEvents.TimeoutEvent):
            if event.name in self.timeouts:
                del self.timeouts[event.name]
            elif event.name in self.cur_task.timeouts:
                del self.cur_task.timeouts[event.name]

        if not self.all_states(event):
            if not self.state_methods[self.state.name](event) and self.cur_task is not None:
                if not self.cur_task.all_states(event) and self.cur_task.state is not None:
                    self.cur_task.state_methods[self.cur_task.state.name](event)

    def start__(self) -> None:
        super(TaskSequence, self).start__()
        task, protocol = self.init_sequence()
        self.switch_task(task, self.init_state(), protocol, {})
        
    def pause__(self) -> None:
        if self.cur_task is not None:
            self.cur_task.pause__()
        super(TaskSequence, self).pause__()

    def stop__(self) -> None:
        if self.cur_task is not None:
            self.cur_task.stop__()
        super(TaskSequence, self).stop__()

    def resume__(self) -> None:
        super(TaskSequence, self).resume__()
        if self.cur_task is not None:
            self.cur_task.resume__()

    def task_complete(self):
        self.log_event(PybEvents.TaskCompleteEvent(self.metadata["chamber"], metadata={"sequence_complete": True}))
