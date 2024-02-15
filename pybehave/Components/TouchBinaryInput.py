from __future__ import annotations
from typing import TYPE_CHECKING, Union, Tuple

if TYPE_CHECKING:
    from pybehave.Tasks.Task import Task
from pybehave.Components.BinaryInput import BinaryInput


class TouchBinaryInput(BinaryInput):

    def __init__(self, task: Task, component_id: str, component_address: str):
        self.definition = None
        super().__init__(task, component_id, component_address)
        self.pos = None

    def update(self, read: Union[Tuple[bool, float], bool]) -> None:
        if isinstance(read, tuple):
            value = read[0]
            pos = read[1]
        else:
            value = read
            pos = None

        if value == self.state:
            repeat = True
        else:
            repeat = False
        self.state = value
        if value and not repeat:
            self.pos = pos
        elif not value and not repeat:
            self.pos = None
