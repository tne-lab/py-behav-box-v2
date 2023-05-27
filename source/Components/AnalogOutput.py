from __future__ import annotations
from typing import TYPE_CHECKING

from Components.Output import Output

if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component


class AnalogOutput(Output):

    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.state = 0

    def set(self, value: float) -> None:
        super(AnalogOutput, self).set(value)

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.ANALOG_OUTPUT
