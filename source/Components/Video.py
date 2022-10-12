from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component
import time


class Video(Component):
    def __init__(self, source: Source, component_id: str, component_address: str):
        self.state = False
        self.name = None
        super().__init__(source, component_id, component_address)

    def start(self) -> None:
        self.name = str(time.time())
        self.state = True
        self.write(self.state)

    def stop(self) -> None:
        self.state = False
        self.write(self.state)

    def get_state(self) -> bool:
        return self.state

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.INPUT
