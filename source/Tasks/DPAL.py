import os
from random import randrange
from enum import Enum

from source.Components.BinaryInput import BinaryInput
from source.Events.InputEvent import InputEvent
from Tasks.Task import Task
from Utilities.touch_in_region import touch_in_region


class DPAL(Task):
    class States(Enum):
        INITIATION = 0
        STIMULUS_PRESENTATION = 1
        TIMEOUT = 2
        INTER_TRIAL_INTERVAL = 3

    class Inputs(Enum):
        INIT_ENTERED = 0
        INIT_EXIT = 1
        FRONT_TOUCH = 2
        MIDDLE_TOUCH = 3
        REAR_TOUCH = 4
        ERROR_TOUCH = 5

    def __init__(self, chamber, source, address_file, protocol):
        super().__init__(chamber, source, address_file, protocol)
        for i in range(len(self.coords)):
            self.coords[i] = (self.coords[i][0], self.coords[i][1] + self.dead_height)
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.image_folder = "{}/py-behav/DPAL/Images/".format(desktop)
        self.cur_trial = 0
        self.state = self.States.INITIATION
        self.fan.toggle(True)
        self.correct_img = None
        self.incorrect_img = None
        self.incorrect_location = None
        self.generate_images()

    def start(self):
        super(DPAL, self).start()
        self.init_light.toggle(True)

    def main_loop(self):
        super().main_loop()
        self.events = []
        init_poke = self.init_poke.check()
        if init_poke == BinaryInput.ENTERED:
            self.events.append(InputEvent(self.Inputs.INIT_ENTERED, self.cur_time - self.start_time))
        elif init_poke == BinaryInput.EXIT:
            self.events.append(InputEvent(self.Inputs.INIT_EXIT, self.cur_time - self.start_time))
        self.touch_screen.get_touches()
        touches = self.touch_screen.handle()
        touch_locs = []
        for touch in touches:
            if touch_in_region(self.coords[0], self.img_dim, touch):
                touch_locs.append(1)
                self.events.append(InputEvent(self.Inputs.FRONT_TOUCH, self.cur_time - self.start_time))
            elif touch_in_region(self.coords[1], self.img_dim, touch):
                touch_locs.append(2)
                self.events.append(InputEvent(self.Inputs.MIDDLE_TOUCH, self.cur_time - self.start_time))
            elif touch_in_region(self.coords[2], self.img_dim, touch):
                touch_locs.append(3)
                self.events.append(InputEvent(self.Inputs.REAR_TOUCH, self.cur_time - self.start_time))
            else:
                touch_locs.append(0)
                self.events.append(InputEvent(self.Inputs.ERROR_TOUCH, self.cur_time - self.start_time))
        if self.state == self.States.INITIATION:
            if init_poke == BinaryInput.ENTERED:
                self.init_light.toggle(False)
                self.change_state(self.States.STIMULUS_PRESENTATION, {"correct_img": self.correct_img, "incorrect_img": self.incorrect_img, "incorrect_location": self.incorrect_location})
                self.touch_screen.add_image(self.image_folder + self.images[self.correct_img],
                                            self.coords[self.correct_img], self.img_dim)
                self.touch_screen.add_image(self.image_folder + self.images[self.incorrect_img],
                                            self.coords[self.incorrect_location], self.img_dim)
                self.touch_screen.refresh()
        elif self.state == self.States.STIMULUS_PRESENTATION:
            if len(touch_locs) > 0 and touch_locs[0] == self.correct_img + 1:
                self.food.dispense()
                self.touch_screen.remove_image(self.image_folder + self.images[self.correct_img])
                self.touch_screen.remove_image(self.image_folder + self.images[self.incorrect_img])
                self.touch_screen.refresh()
                self.generate_images()
                self.cur_trial += 1
                self.tone.play_sound(1800, 1, 1)
                self.change_state(self.States.INTER_TRIAL_INTERVAL, {"response": "correct"})
            elif len(touch_locs) > 0 and touch_locs[0] == self.incorrect_location + 1:
                self.cage_light.toggle(True)
                self.touch_screen.remove_image(self.image_folder + self.images[self.correct_img])
                self.touch_screen.remove_image(self.image_folder + self.images[self.incorrect_img])
                self.touch_screen.refresh()
                self.tone.play_sound(1200, 1, 1)
                self.change_state(self.States.TIMEOUT, {"response": "incorrect"})
        elif self.state == self.States.TIMEOUT:
            if self.cur_time - self.entry_time > self.timeout_duration:
                self.cage_light.toggle(False)
                self.change_state(self.States.INTER_TRIAL_INTERVAL)
        elif self.state == self.States.INTER_TRIAL_INTERVAL:
            if self.cur_time - self.entry_time > self.inter_trial_interval:
                self.init_light.toggle(True)
                self.change_state(self.States.INITIATION)

    def get_variables(self):
        return {
            'max_duration': 60,
            'max_correct': 100,
            'inter_trial_interval': 10,
            'timeout_duration': 5,
            'images': ['6B.bmp', '6A.bmp', '2A.bmp'],
            'coords': [(61, 10), (371, 10), (681, 10)],
            'img_dim': (290, 290),
            'dead_height': 0
        }

    def is_complete(self):
        return self.cur_trial >= self.max_correct or self.cur_time - self.start_time > self.max_duration * 60

    def generate_images(self):
        locs = list(range(len(self.images)))
        self.correct_img = randrange(len(self.images))
        del locs[self.correct_img]
        ind = randrange(len(self.images) - 1)
        self.incorrect_img = locs[ind]
        del locs[ind]
        self.incorrect_location = locs[0]
