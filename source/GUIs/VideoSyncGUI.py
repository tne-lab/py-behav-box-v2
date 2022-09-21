from typing import List

from Elements.Element import Element
from GUIs import Colors
from GUIs.GUI import GUI


class VideoSyncGUI(GUI):

    def draw(self):
        self.task_gui.fill(Colors.darkgray)

    def get_elements(self) -> List[Element]:
        return []
