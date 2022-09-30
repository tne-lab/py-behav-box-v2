from typing import List
from types import MethodType

from Elements.CircleLightElement import CircleLightElement
from Elements.Element import Element
from Elements.NosePokeElement import NosePokeElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from GUIs import Colors
from GUIs.GUI import GUI


class MiddleNosePokeTrainingGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.np_lights = []
        self.np_inputs = []
        self.info_boxes = []

        def feed_mouse_up(self, _):
            self.clicked = False
            task.food.dispense()
            task.pokes = 0

        def pellets_text(self):
            return [str(task.food.count)]

        def trial_count_text(self):
            return [str(task.pokes)]

        def time_in_trial_text(self):
            return [str(round(task.time_elapsed()))]

        for i in range(3):
            npl = CircleLightElement(self.task_gui, self.SF * (50 + (i + 1) * (25 + 60)), self.SF * 60, self.SF * 30,
                                     Colors.lightgray, Colors.darkgray, task.nose_poke_lights[i])
            self.np_lights.append(npl)
            npi = NosePokeElement(self.task_gui, self.SF * (50 + (i + 1) * (25 + 60)), self.SF * 150, self.SF * 30,
                                  task.nose_pokes[i])
            self.np_inputs.append(npi)
        self.feed_button = ButtonElement(self.task_gui, self.SF * 225, self.SF * 500, self.SF * 50, self.SF * 20,
                                         "FEED", task.food, int(self.SF * 12))
        self.feed_button.mouse_up = MethodType(feed_mouse_up, self.feed_button)
        pellets = InfoBoxElement(self.task_gui, self.SF * 225, self.SF * 450, self.SF * 50, self.SF * 15, "PELLETS",
                                 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        pellets.get_text = MethodType(pellets_text, pellets)
        self.info_boxes.append(pellets)
        time_in_trial = InfoBoxElement(self.task_gui, self.SF * 400, self.SF * 450, self.SF * 50, self.SF * 15, "TIME",
                                       'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        time_in_trial.get_text = MethodType(time_in_trial_text, time_in_trial)
        self.info_boxes.append(time_in_trial)
        trial_count = InfoBoxElement(self.task_gui, self.SF * 400, self.SF * 500, self.SF * 50, self.SF * 15, "POKES",
                                     'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        trial_count.get_text = MethodType(trial_count_text, trial_count)
        self.info_boxes.append(trial_count)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [*self.np_lights, *self.np_inputs, self.feed_button, *self.info_boxes]
