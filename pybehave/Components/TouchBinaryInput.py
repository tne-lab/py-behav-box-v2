from __future__ import annotations
from typing import TYPE_CHECKING, Union, Tuple

if TYPE_CHECKING:
    from pybehave.Tasks.Task import Task
from pybehave.Components.BinaryInput import BinaryInput


class TouchBinaryInput(BinaryInput):

    def __init__(self, task: Task, component_id: str, component_address: str):
        super().__init__(task, component_id, component_address)
        self.pos = None

    def update(self, read: Union[Tuple[bool, float], bool]) -> bool:
        if isinstance(read, tuple) or isinstance(read, list):
            value = read[0]
            pos = read[1]
        else:
            value = read
            pos = None

        if value == self.state:
            return False
        else:
            self.state = value
            if value:
                self.pos = pos
            else:
                self.pos = None
            return True
