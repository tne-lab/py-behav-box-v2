from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Type, Dict, List

from Components.Component import Component
from Events import PybEvents
from Tasks.Task import Task
import time

from Utilities.create_task import create_task


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
                elif len(components[name]) < len(sub_components[name]):
                    components[name] = sub_components[name]
        components.update(self.get_sequence_components())
        return components

    def switch_task(self, task: Type[Task], protocol: str, new_state: Enum = None, metadata: Any = None) -> None:
        create_task(self.switch_task_(task, protocol, new_state, metadata))

    async def switch_task_(self, task: Type[Task], protocol: str, new_state: Enum = None, metadata: Any = None) -> None:
        if self.cur_task is not None:
            self.cur_task.stop()
        if new_state is not None and new_state != self.state:
            self.change_state(new_state, metadata)
        self.cur_task = await self.ws.switch_task(self, task, protocol)
        self.log_event(PybEvents.StartEvent(self.cur_task, metadata))

    def main_loop(self, event: PybEvents.PybEvent) -> None:
        self.cur_time = time.perf_counter()
        if isinstance(event, PybEvents.StateEnterEvent) and event.task is self:
            self.state = event.state
        elif isinstance(event, PybEvents.StateExitEvent) and event.task is self:
            if self.state in self.state_timeouts:
                for tm in self.state_timeouts[self.state].values():
                    if tm[1]:
                        tm[0].stop()
        all_handled = self.all_states(event)
        if not all_handled and hasattr(self, self.state.name):
            state_method = getattr(self, self.state.name)
            all_handled = state_method(event)
        if not all_handled and self.cur_task is not None and self.cur_task.started:
            self.cur_task.main_loop(event)

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
