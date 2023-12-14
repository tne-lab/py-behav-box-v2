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

    @abstractmethod
    def init_sequence(self):
        raise NotImplementedError

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
        sub_metadata = metadata.copy()
        sub_metadata["protocol"] = protocol
        sub_metadata["sub_task"] = str(task)

        if self.state != seq_state:
            self.change_state(seq_state, metadata)
        self.log_event(PybEvents.StartEvent(self.metadata["chamber"], metadata=sub_metadata), sequence=False)

    def main_loop(self, event: PybEvents.PybEvent) -> None:
        if "sequence" in event.metadata:
            super(TaskSequence, self).main_loop(event)
        else:
            if not self.all_states(event):
                self.state_methods[self.state.name](event)
            if not isinstance(event, PybEvents.TaskCompleteEvent) and self.cur_task is not None:
                self.cur_task.main_loop(event)
            if self.is_complete_():
                self.task_complete()

    def start__(self) -> Dict:
        metadata = super(TaskSequence, self).start__()
        task, protocol = self.init_sequence()
        self.switch_task(task, self.init_state(), protocol, {})
        return metadata
        
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

    def log_event(self, event: PybEvents.TaskEvent, sequence=True):
        if sequence:
            event.metadata["sequence"] = True
        self.tp.tp_q.append(event)
