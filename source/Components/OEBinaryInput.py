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

    def check(self) -> int:
        json_strs = self.source.read_component(self.id)
        if len(json_strs) > 0:
            for json_str in reversed(json_strs):
                if self.rising and self.falling:
                    if not self.state and json_str['metaData']['Direction'] == '1' and json_str['data']:
                        self.state = True
                        return self.ENTERED
                    elif self.state and json_str['metaData']['Direction'] == '0' and not json_str['data']:
                        self.state = False
                        return self.EXIT
                else:
                    if not self.state and json_str['data']:
                        self.state = True
                        return self.ENTERED
                    elif self.state and not json_str['data']:
                        self.state = False
                        return self.EXIT
        return self.NO_CHANGE
