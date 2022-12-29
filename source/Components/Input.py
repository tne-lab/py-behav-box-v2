from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component


class Input(Component):

    def __init__(self, source: Source, component_id: str, component_address: str):
        self.state = None
        super().__init__(source, component_id, component_address)

    def check(self) -> Any:
        value = self.source.read_component(self.id)
        self.state = value
        return self.state

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.INPUT
