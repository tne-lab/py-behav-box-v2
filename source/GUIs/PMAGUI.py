from typing import List
from types import MethodType
import math
from enum import Enum

from Elements.BarPressElement import BarPressElement
from Elements.IndicatorElement import IndicatorElement
from Elements.Element import Element
from Elements.SoundElement import SoundElement
from Elements.ShockElement import ShockElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from Events.InputEvent import InputEvent
from GUIs import Colors
from GUIs.GUI import GUI
from Tasks.PMA import PMA


class PMAGUI(GUI):
    class Inputs(Enum):
        GUI_PELLET = 0

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def feed_mouse_up(self, _):
            self.clicked = False
            task.food.dispense()
            task.events.append(task, InputEvent(PMAGUI.Inputs.GUI_PELLET))

        def pellets_text(self):
            return [str(task.food.pellets)]

        def presses_text(self):
            return [str(task.presses)]

        def tone_count_text(self):
            return [str(task.cur_trial)]

        def reward_available(self):
            return task.food_light.get_state()

        def next_event(self):
            if task.state == PMA.States.INTER_TONE_INTERVAL:
                if task.random:
                    return [str(math.ceil(task.iti - task.time_in_state()))]
                else:
                    return [str(math.ceil(task.time_sequence[task.cur_trial] - task.time_in_state()))]
            elif task.state == PMA.States.TONE:
                return [str(math.ceil(task.tone_duration - task.time_in_state()))]
            elif task.state == PMA.States.SHOCK:
                return [str(math.ceil(task.shock_duration - task.time_in_state()))]
            elif task.state == PMA.States.POST_SESSION:
                return [str(math.ceil(task.post_session_time - task.time_in_state()))]
            else:
                return [str(0)]

        def event_countup(self):
            return [str(round(task.time_elapsed() / 60, 2))]

        self.lever = BarPressElement(self.task_gui, self.SF * 77, self.SF * 25, self.SF * 100, self.SF * 90, task.food_lever)
        self.feed_button = ButtonElement(self.task_gui, self.SF * 129, self.SF * 170, self.SF * 50, self.SF * 20, "FEED", task.food, int(self.SF * 12))
        self.feed_button.mouse_up = MethodType(feed_mouse_up, self.feed_button)
        presses = InfoBoxElement(self.task_gui, self.SF * 69, self.SF * 125, self.SF * 50, self.SF * 15, "PRESSES",
                                 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        presses.get_text = MethodType(presses_text, presses)
        self.info_boxes.append(presses)
        pellets = InfoBoxElement(self.task_gui, self.SF * 129, self.SF * 125, self.SF * 50, self.SF * 15, "PELLETS", 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        pellets.get_text = MethodType(pellets_text, pellets)
        self.info_boxes.append(pellets)
        tone_count = InfoBoxElement(self.task_gui, self.SF * 242, self.SF * 125, self.SF * 50, self.SF * 15, "NTONE", 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        tone_count.get_text = MethodType(tone_count_text, tone_count)
        self.info_boxes.append(tone_count)
        ne = InfoBoxElement(self.task_gui, self.SF * 372, self.SF * 125, self.SF * 50, self.SF * 15, "NEXT EVENT", 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        ne.get_text = MethodType(next_event, ne)
        self.info_boxes.append(ne)
        ec = InfoBoxElement(self.task_gui, self.SF * 372, self.SF * 170, self.SF * 50, self.SF * 15, "TIME", 'BOTTOM', ['0'], int(self.SF * 14), self.SF)
        ec.get_text = MethodType(event_countup, ec)
        self.info_boxes.append(ec)
        self.reward_indicator = IndicatorElement(self.task_gui, self.SF * 74, self.SF * 163, self.SF * 15, Colors.green, Colors.red)
        self.reward_indicator.on = MethodType(reward_available, self.reward_indicator)
        self.tone = SoundElement(self.task_gui, self.SF * 227, self.SF * 25, self.SF * 40, task.tone)
        self.shocker = ShockElement(self.task_gui, self.SF * 357, self.SF * 25, self.SF * 40, (255, 255, 0), task.shocker)

    def draw(self):
        self.task_gui.fill(Colors.darkgray)
        for el in self.get_elements():
            el.draw()

    def get_elements(self) -> List[Element]:
        return [self.feed_button, *self.info_boxes, self.lever, self.reward_indicator, self.tone, self.shocker]
