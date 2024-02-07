from __future__ import annotations
from typing import TYPE_CHECKING

from Components.Output import Output

if TYPE_CHECKING:
    from Tasks.Task import Task

from Components.Component import Component


class AnalogOutput(Output):

    def __init__(self, task: Task, component_id: str, component_address: str):
        super().__init__(task, component_id, component_address)
        self.state = 0

    def write(self, value: float) -> None:
        super(AnalogOutput, self).write(value)

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.ANALOG_OUTPUT
