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
        self.out_paths = {}
        self.cur_frames = {}
        self.frame_times = {}
        self.do_close = {}
        self.available = True
        vt = threading.Thread(target=self.run, args=[])
        vt.start()

    def register_component(self, task, component):
        self.components[component.id] = component
        self.caps[component.id] = cv2.VideoCapture(int(component.address), cv2.CAP_DSHOW)
        self.outs[component.id] = None
        self.cur_frames[component.id] = None
        self.frame_times[component.id] = time.perf_counter()
        self.do_close[component.id] = False
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.out_paths[component.id] = "{}\\py-behav\\{}\\".format(desktop, type(task).__name__)
        if not self.caps[component.id].isOpened():
            print('error opening vid')

    def close_source(self):
        self.available = False

    def close_component(self, component_id):
        self.do_close[component_id] = True

    def read_component(self, component_id):
        return self.cur_frames[component_id]

    def write_component(self, component_id, msg):
        self.recs[component_id] = msg

    def run(self):
        while self.available:
            for vid in list(self.caps):
                if self.do_close[vid]:
                    cv2.destroyAllWindows()
                    self.caps[vid].release()
                    if self.outs[vid] is not None:
                        self.outs[vid].release()
                    del self.caps[vid]
                    del self.outs[vid]
                    del self.components[vid]
                    del self.cur_frames[vid]
                    del self.frame_times[vid]
                    del self.out_paths[vid]
                    del self.do_close[vid]
                elif self.caps[vid].isOpened() and time.perf_counter() - self.frame_times[vid] > 1 / int(
                        self.components[vid].fr):
                    ret, self.cur_frames[vid] = self.caps[vid].read()
                    if ret:
                        self.frame_times[vid] = self.frame_times[vid] + 1 / int(self.components[vid].fr)
                        cv2.namedWindow(self.components[vid].address)
                        cv2.imshow(self.components[vid].address, self.cur_frames[vid])

                        if self.components[vid].get_state():
                            if self.outs[vid] is None:
                                fourcc = cv2.VideoWriter_fourcc(*'XVID')  # for AVI files
                                if not os.path.exists(self.out_paths[vid] + "Videos"):
                                    os.makedirs(self.out_paths[vid] + "Videos")
                                self.outs[vid] = cv2.VideoWriter(self.out_paths[vid] + "Videos\\" + self.components[vid].name + ".avi", fourcc,
                                                                 int(self.components[vid].fr), (
                                                                     int(self.caps[vid].get(3)),
                                                                     int(self.caps[vid].get(4))))
                            self.outs[vid].write(self.cur_frames[vid])

                        # Do we need this?
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            self.caps[vid].release()
                            cv2.destroyAllWindows()  # Don't want to destroy all
                            try:
                                self.outs[vid].release()
                            except:
                                pass
        cv2.destroyAllWindows()
        for vid in self.caps.keys():
            self.caps[vid].release()
            if self.outs[vid] is not None:
                self.outs[vid].release()
