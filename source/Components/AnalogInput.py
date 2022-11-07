from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component


class AnalogInput(Component):

    def __init__(self, source: Source, component_id: str, component_address: str):
        self.state = 0
        super().__init__(source, component_id, component_address)

    def check(self) -> int:
        value = self.source.read_component(self.id)
        self.state = value
        return self.state

    def get_state(self) -> int:
        return self.state

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.ANALOG_INPUT
