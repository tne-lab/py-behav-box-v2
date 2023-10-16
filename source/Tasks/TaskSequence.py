from abc import ABCMeta, abstractmethod
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

    def get_components(self) -> Dict[str, List[Type[Component]]]:
        components = {}
        for task in self.get_tasks():
            sub_components = task.get_components()
            for name in sub_components:
                if name not in components:
                    components[name] = sub_components[name]
        components.update(self.get_sequence_components())
        return components

    def switch_task(self, task: Type[Task], protocol: str, metadata: Any = None) -> None:
        if self.cur_task is not None:
            self.cur_task.stop()
        self.cur_task = task()
        self.cur_task.initialize(self, self.components, protocol)
        metadata = metadata.copy()
        metadata["sub_task"] = str(task)
        self.log_event(PybEvents.StartEvent(self.metadata["chamber"], metadata=metadata))

    def main_loop(self, event: PybEvents.PybEvent) -> None:
        if isinstance(event, PybEvents.StateEnterEvent):
            self.state = self.States(event.value)
        elif isinstance(event, PybEvents.StateExitEvent):
            if self.state in self.state_timeouts:
                for tm in self.state_timeouts[self.state].values():
                    if tm[1]:
                        self.cancel_timeout(tm[0].name)
        elif isinstance(event, PybEvents.TimeoutEvent):
            del self.timeouts[event.name]
        all_handled = self.all_states(event)
        if not all_handled and self.state.name in self.state_methods:
            if not self.state_methods[self.state.name](event) and self.cur_task is not None:
                self.cur_task.state_methods[self.cur_task.state.name](event)

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
        self.log_event(PybEvents.TaskCompleteEvent(self.metadata["chamber"], {"sequence_complete": True}))
