from __future__ import annotations
from typing import TYPE_CHECKING

from Components.Input import Input

if TYPE_CHECKING:
    from Sources.Source import Source

from Components.Component import Component


class BinaryInput(Input):

    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.state = False

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.DIGITAL_INPUT
