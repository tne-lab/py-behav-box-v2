from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pybehave.Tasks.Task import Task

from pybehave.Components.Component import Component
import time


class Video(Component):
    def __init__(self, task: Task, component_id: str, component_address: str):
        super().__init__(task, component_id, component_address)
        self.state = False
        self.name = None

    def start(self) -> None:
        if not self.state:
            if self.name is None:
                self.name = str(time.time())
            self.state = True
            self.write(self.state)

    def stop(self) -> None:
        if self.state:
            self.state = False
            self.write(self.state)

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.BOTH
