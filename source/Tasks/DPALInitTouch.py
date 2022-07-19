import os
from random import randrange
from enum import Enum
from statistics import mode

from Events.InputEvent import InputEvent
from Tasks.Task import Task
from Utilities.touch_in_region import touch_in_region


class DPALInitTouch(Task):
    class States(Enum):
        STIMULUS_PRESENTATION = 0
        INTER_TRIAL_INTERVAL = 1

    class Inputs(Enum):
        FRONT_TOUCH = 2
        MIDDLE_TOUCH = 3
        REAR_TOUCH = 4
        ERROR_TOUCH = 5

    def __init__(self, *args):
        super().__init__(*args)
        for i in range(len(self.coords)):
            self.coords[i] = (self.coords[i][0], self.coords[i][1] + self.dead_height)
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.image_folder = "{}/py-behav/DPAL/Images/".format(desktop)
        self.cur_trial = 0
        self.correct_locations = [None] * self.max_repeats
        self.generate_images()

    def start(self):
        self.state = self.States.STIMULUS_PRESENTATION
        self.fan.toggle(True)
        self.touch_screen.add_image(self.image_folder + self.blank, self.coords[self.correct_locations[-1]],
                                    self.img_dim)
        self.touch_screen.refresh()
        super(DPALInitTouch, self).start()

    def main_loop(self):
        super().main_loop()
        self.touch_screen.get_touches()
        touches = self.touch_screen.handle()
        touch_locs = []
        for touch in touches:
            if touch_in_region(self.coords[0], self.img_dim, touch):
                touch_locs.append(1)
                self.events.append(InputEvent(self, self.Inputs.FRONT_TOUCH))
            elif touch_in_region(self.coords[1], self.img_dim, touch):
                touch_locs.append(2)
                self.events.append(InputEvent(self, self.Inputs.MIDDLE_TOUCH))
            elif touch_in_region(self.coords[2], self.img_dim, touch):
                touch_locs.append(3)
                self.events.append(InputEvent(self, self.Inputs.REAR_TOUCH))
            else:
                touch_locs.append(0)
                self.events.append(InputEvent(self, self.Inputs.ERROR_TOUCH))
        if self.state == self.States.STIMULUS_PRESENTATION:
            if len(touch_locs) > 0 and touch_locs[0] == self.correct_locations[-1] + 1:
                self.food.dispense()
                self.touch_screen.remove_image(self.image_folder + self.blank)
                self.touch_screen.refresh()
                self.generate_images()
                self.cur_trial += 1
                self.tone.play_sound(1800, 1, 1)
                self.change_state(self.States.INTER_TRIAL_INTERVAL, {"response": "correct"})
            elif not self.must_touch and self.time_in_state() > self.stimulus_duration:
                self.food.dispense()
                self.touch_screen.remove_image(self.image_folder + self.blank)
                self.touch_screen.refresh()
                self.generate_images()
                self.tone.play_sound(1800, 1, 1)
                self.change_state(self.States.INTER_TRIAL_INTERVAL, {"response": "none"})
        elif self.state == self.States.INTER_TRIAL_INTERVAL:
            if self.time_in_state() > self.inter_trial_interval:
                self.change_state(self.States.STIMULUS_PRESENTATION, {"correct_location": self.correct_locations[-1]})
                self.touch_screen.add_image(self.image_folder + self.blank, self.coords[self.correct_locations[-1]],
                                            self.img_dim)
                self.touch_screen.refresh()

    def get_variables(self):
        return {
            'max_duration': 60,
            'max_correct': 30,
            'inter_trial_interval': 10,
            'stimulus_duration': 30,
            'blank': 'BLANK.bmp',
            'coords': [(61, 10), (371, 10), (681, 10)],
            'img_dim': (290, 290),
            'dead_height': 0,
            'max_repeats': 3,
            'must_touch': True
        }

    def is_complete(self):
        return self.cur_trial >= self.max_correct or self.time_elapsed() > self.max_duration * 60

    def generate_images(self):
        locs = list(range(len(self.coords)))
        most_common = mode(self.correct_locations)
        count = self.correct_locations.count(most_common)
        if most_common is not None and count == self.max_repeats:
            del locs[most_common]
        self.correct_locations.pop(0)
        self.correct_locations.append(locs[randrange(len(locs))])
