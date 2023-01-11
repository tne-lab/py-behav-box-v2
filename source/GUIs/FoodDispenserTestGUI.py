from types import MethodType
from typing import List

from Elements.Element import Element
from GUIs.GUI import GUI

from Elements.InfoBoxElement import InfoBoxElement


class FoodDispenserTestGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def next_event(self):
            return [str(task.food.count)]

        ne = InfoBoxElement(self, 200, 125, 100, 30, "DELIVERED", 'BOTTOM', ['0'], f_size=28)
        ne.get_text = MethodType(next_event, ne)
        self.info_boxes.append(ne)

    def get_elements(self) -> List[Element]:
        return [*self.info_boxes]
