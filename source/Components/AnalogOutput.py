from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component


class AnalogOutput(Component):

    def __init__(self, source: Source, component_id: str, component_address: str):
        self.state = 0
        super().__init__(source, component_id, component_address)

    def set(self, value: int) -> None:
        self.source.write_component(self.id, value)
        self.state = value

    def get_state(self) -> int:
        return self.state

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.ANALOG_OUTPUT
