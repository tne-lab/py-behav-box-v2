from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source

from Components.BinaryInput import BinaryInput


class OEBinaryInput(BinaryInput):

    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.rising = True
        self.falling = False

    def update(self, value: dict) -> None:
        if self.rising and self.falling:
            if not self.state and value['metaData']['Direction'] == '1' and value['data']:
                self.state = True
            elif self.state and value['metaData']['Direction'] == '0' and not value['data']:
                self.state = False
        else:
            if not self.state and value['data']:
                self.state = True
            elif self.state and not value['data']:
                self.state = False
