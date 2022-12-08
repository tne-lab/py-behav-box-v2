from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source

from Utilities.ScreenInterface import ScreenInterface

from Components.BinaryInput import BinaryInput
from Components.Component import Component


class TouchBinaryInput(BinaryInput, ScreenInterface):

    def __init__(self, source: Source, component_id: str, component_address: str):
        self.definition = None
        super().__init__(source, component_id, component_address)
        self.pos = None
        self.hidden = None

    def check(self) -> int:
        read = self.source.read_component(self.id)
        if read is tuple:
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
            return self.ENTERED
        elif not value and not repeat:
            self.pos = None
            return self.EXIT
        else:
            return self.NO_CHANGE

    def show(self):
        if self.hidden:
            self.source.write_component(self.id, True)

    def hide(self):
        if not self.hidden:
            self.source.write_component(self.id, False)

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.BOTH