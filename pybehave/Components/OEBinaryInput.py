from __future__ import annotations
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from pybehave.Tasks.Task import Task

from pybehave.Components.BinaryInput import BinaryInput


class OEBinaryInput(BinaryInput):

    def __init__(self, task: Task, component_id: str, component_address: str):
        super().__init__(task, component_id, component_address)
        self.rising = True
        self.falling = False

    def update(self, value: dict) -> bool:
        if self.rising and self.falling:
            if not self.state and value['metaData']['Direction'] == '1' and value['data']:
                self.state = True
                return True
            elif self.state and value['metaData']['Direction'] == '0' and not value['data']:
                self.state = False
                return True
        else:
            if not self.state and value['data']:
                self.state = True
                return True
            elif self.state and not value['data']:
                self.state = False
                return True
        return False

    @staticmethod
    def metadata_defaults() -> Dict:
        return {"rising": True, "falling": False}
