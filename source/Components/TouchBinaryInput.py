from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source
from Components.BinaryInput import BinaryInput


class TouchBinaryInput(BinaryInput):

    def __init__(self, source: Source, component_id: str, component_address: str):
        self.definition = None
        super().__init__(source, component_id, component_address)
        self.pos = None

    def check(self) -> int:
        read = self.source.read_component(self.id)
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
            return self.ENTERED
        elif not value and not repeat:
            self.pos = None
            return self.EXIT
        else:
            return self.NO_CHANGE
