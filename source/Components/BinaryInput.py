from __future__ import annotations
from typing import TYPE_CHECKING

from Components.Input import Input

if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component


class BinaryInput(Input):

    NO_CHANGE = 0
    ENTERED = 1
    EXIT = 2

    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.state = False

    def check(self) -> int:
        value = self.source.read_component(self.id)
        if value == self.state:
            repeat = True
        else:
            repeat = False
        self.state = value
        if value and not repeat:
            return self.ENTERED
        elif not value and not repeat:
            return self.EXIT
        else:
            return self.NO_CHANGE

    # For simulation control
    def toggle(self, on: bool) -> None:
        self.source.write_component(self.id, on)

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.DIGITAL_INPUT
