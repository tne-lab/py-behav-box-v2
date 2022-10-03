from typing import List
from types import MethodType
import math

from Elements.BarPressElement import BarPressElement
from Elements.IndicatorElement import IndicatorElement
from Elements.Element import Element
from Elements.SoundElement import SoundElement
from Elements.ShockElement import ShockElement
from Elements.ButtonElement import ButtonElement
from Elements.InfoBoxElement import InfoBoxElement
from GUIs import Colors
from GUIs.GUI import GUI
from Tasks.FearConditioning import FearConditioning


class FearConditioningGUI(GUI):

    def __init__(self, task_gui, task):
        super().__init__(task_gui, task)
        self.info_boxes = []

        def feed_mouse_up(self, _):
            self.clicked = False
            task.food.toggle(task.dispense_time)

        def pellets_text(self):
            return [str(task.food.count)]

        def tone_count_text(self):
            return [str(task.cur_trial)]

        def reward_available(self):
            return task.reward_available

        def vi_countdown(self):
            return [str(max([0, math.ceil(task.reward_lockout - (task.cur_time - task.prev_reward_time))]))]

        def next_event(self):
            if not task.state == FearConditioning.States.TONE:
                return [str(task.time_sequence[task.cur_trial * 2])]
            else:
                return [str(task.time_sequence[task.cur_trial * 2 + 1])]

        def event_countup(self):
            return [str(math.ceil(task.time_elapsed()))]

        self.lever = BarPressElement(self, 77, 25, 100, 90, comp=task.food_lever)
        self.feed_button = ButtonElement(self, 129, 170, 50, 20, "FEED")
        self.feed_button.mouse_up = MethodType(feed_mouse_up, self.feed_button)
        pellets = InfoBoxElement(self, 129, 125, 50, 15, "PELLETS", 'BOTTOM', ['0'])
        pellets.get_text = MethodType(pellets_text, pellets)
        self.info_boxes.append(pellets)
        tone_count = InfoBoxElement(self, 242, 125, 50, 15, "NTONE", 'BOTTOM', ['0'])
        tone_count.get_text = MethodType(tone_count_text, tone_count)
        self.info_boxes.append(tone_count)
        ne = InfoBoxElement(self, 372, 125, 50, 15, "NEXT EVENT", 'BOTTOM', ['0'])
        ne.get_text = MethodType(next_event, ne)
        self.info_boxes.append(ne)
        ec = InfoBoxElement(self, 372, 170, 50, 15, "TIME", 'BOTTOM', ['0'])
        ec.get_text = MethodType(event_countup, ec)
        self.info_boxes.append(ec)
        vic = InfoBoxElement(self, 64, 125, 50, 15, "VI COUNT", 'BOTTOM', ['0'])
        vic.get_text = MethodType(vi_countdown, vic)
        self.info_boxes.append(vic)
        self.reward_indicator = IndicatorElement(self, 74, 163, 15)
        self.reward_indicator.on = MethodType(reward_available, self.reward_indicator)
        self.tone = SoundElement(self, 227, 25, 40, comp=task.tone)
        self.shocker = ShockElement(self, 357, 25, 40, comp=task.shocker)

    def get_elements(self) -> List[Element]:
        return [self.feed_button, *self.info_boxes, self.lever, self.reward_indicator, self.tone, self.shocker]
