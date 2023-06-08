from __future__ import annotations
from typing import TYPE_CHECKING

from Components.Output import Output

if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component
import time


class Video(Component):
    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.state = False
        self.name = None

    def start(self) -> None:
        if not self.state:
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
