from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component


class Output(Component):

    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.state = None

    def set(self, value: Any) -> None:
        self.source.write_component(self.id, value)
        self.state = value

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.OUTPUT
