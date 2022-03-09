import os
import threading
import time

import cv2

from Sources.Source import Source


class VideoSource(Source):
    def __init__(self):
        self.components = {}
        self.caps = {}
        self.recs = {}
        self.outs = {}
        self.cur_frames = {}
        self.frame_times = {}
        self.available = True
        vt = threading.Thread(target=self.run, args=[])
        vt.start()

    def register_component(self, task, component):
        self.components[component.id] = component
        self.caps[component.id] = cv2.VideoCapture(int(component.address), cv2.CAP_DSHOW)
        self.recs[component.id] = False
        self.cur_frames[component.id] = None
        self.frame_times[component.id] = time.perf_counter()
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # for AVI files
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        task_folder = "{}/py-behav/{}/".format(desktop, type(task).__name__)
        if not self.caps[component.id].isOpened():
            print('error opening aux vid, probably doesn\'t exist')
        # self.outs[component.id] = cv2.VideoWriter(task_folder + "Videos/test.avi", fourcc, int(component.fr), (int(self.caps[component.id].width), int(self.caps[component.id].height)))

    def close_source(self):
        self.available = False
        cv2.destroyAllWindows()
        for vid in self.caps.keys():
            self.caps[vid].release()
            self.outs[vid].release()

    def read_component(self, component_id):
        return self.cur_frames[component_id]

    def write_component(self, component_id, msg):
        self.recs[component_id] = msg

    def run(self):
        while self.available:
            for vid in self.caps.keys():
                if self.caps[vid].isOpened() and time.perf_counter() - self.frame_times[vid] > 1 / int(self.components[vid].fr):
                    self.frame_times[vid] = self.frame_times[vid] + 1 / int(self.components[vid].fr)
                    ret, self.cur_frames[vid] = self.caps[vid].read()
                    cv2.namedWindow(self.components[vid].address)
                    cv2.imshow(self.components[vid].address, self.cur_frames[vid])

                    if self.recs[vid]:
                        self.outs[vid].write(self.cur_frames[vid])

                    # Do we need this?
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.caps[vid].release()
                        cv2.destroyAllWindows()  # Don't want to destroy all
                        try:
                            self.outs[vid].release()
                        except:
                            pass
