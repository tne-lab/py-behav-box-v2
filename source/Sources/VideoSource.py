from datetime import datetime
import os
import threading
import time

import cv2

from Sources.Source import Source
from Utilities.Exceptions import ComponentRegisterError


class VideoSource(Source):
    """
        Class defining a Source for interacting with National Instruments DAQs.

        Attributes
        ----------
        components : dict
            Links Component IDs to Component objects
        caps : dict
            Links Component IDs to VideoCapture objects
        outs : dict
            Links Component IDs to VideoWriter objects
        out_paths : dict
            Links Component IDs to output paths for video files
        cur_frames : dict
            Links Component IDs to the currently acquired video frame
        frame_times : dict
            Links Component IDs to the time the last frame was acquired
        do_close : dict
            Links Component IDs to an indicator if they should be closed
        available : bool
            Boolean indicating if video is currently being acquired

        Methods
        -------
        register_component(task, component)
            Sets up a connection to the provided camera address
        close_source()
            Stops video acquisition
        close_component(component_id)
            Flags that the indicated component should be closed
        read_component(component_id)
            Returns the most recently acquired frame for the indicated Component
        write_component(component_id, msg)
            No functionality
        run()
            Function run continuously in video thread for coordinating acqusition, saving, and control
    """

    def __init__(self):
        super(VideoSource, self).__init__()
        self.available = True
        self.caps = {}
        self.outs = {}
        self.out_paths = {}
        self.cur_frames = {}
        self.frame_times = {}
        self.do_close = {}
        self.tasks = {}
        vt = threading.Thread(target=self.run, args=[])
        vt.start()

    def register_component(self, task, component):
        self.components[component.id] = component
        self.caps[component.id] = VideoThread(component.address)
        self.outs[component.id] = None
        self.cur_frames[component.id] = None
        self.frame_times[component.id] = time.perf_counter()
        self.do_close[component.id] = False
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.out_paths[component.id] = "{}\\py-behav\\{}\\Data\\{{}}\\{{}}\\".format(desktop, type(task).__name__)
        self.tasks[component.id] = task
        if not self.caps[component.id].isOpened():
            self.do_close[component.id] = True
            raise ComponentRegisterError
        else:
            self.caps[component.id].start()

    def close_source(self):
        self.available = False

    def close_component(self, component_id):
        self.do_close[component_id] = True

    def read_component(self, component_id):
        return self.cur_frames[component_id]

    def run(self):
        # While video is being acquired
        while self.available:
            # Iterate over registered cameras
            for vid in list(self.caps):
                # Removes all objects associated with camera flagged for closing
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
                    del self.tasks[vid]
                # If the camera is available and more than a frame has passed since the last acquisition
                elif self.caps[vid].isOpened():
                    while time.perf_counter() - self.frame_times[vid] > 1 / int(self.components[vid].fr):
                        # Update the time when the last frame was acquired
                        self.frame_times[vid] = self.frame_times[vid] + 1 / int(self.components[vid].fr)
                        # Create a window for the video frame
                        cv2.namedWindow(self.components[vid].address)
                        cv2.imshow(self.components[vid].address, self.caps[vid].frame)

                        # If video should be saved
                        if self.components[vid].get_state():
                            # If an output object has not yet been created, generate a VideoWriter
                            if self.outs[vid] is None:
                                fourcc = cv2.VideoWriter_fourcc(*'XVID')  # for AVI files
                                self.outs[vid] = cv2.VideoWriter(
                                    self.out_paths[vid].format(self.tasks[vid].metadata["subject"], datetime.now().strftime("%m-%d-%Y")) + self.components[vid].name + ".avi", fourcc,
                                    int(self.components[vid].fr), self.caps[vid].dims)
                            # Write the current frame to the output file
                            self.outs[vid].write(self.caps[vid].frame)
                        # If the video should not be saved and there is an active VIdeoWriter, close the writer
                        elif self.outs[vid] is not None:
                            self.outs[vid].release()
                            self.outs[vid] = None

                        # Refresh cv2
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

    def is_available(self):
        return self.available


class VideoThread(threading.Thread):

    def __init__(self, src):
        super(VideoThread, self).__init__()
        self.stream = cv2.VideoCapture(int(src), cv2.CAP_DSHOW)
        (self.grabbed, self.frame) = self.stream.read()
        self.dims = (int(self.stream.get(3)), int(self.stream.get(4)))
        self.stopped = False

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def start(self):
        threading.Thread(target=self.get, args=()).start()
        return self

    def stop(self):
        self.stopped = True

    def isOpened(self):
        return self.stream.isOpened()

    def release(self):
        self.stop()
        self.stream.release()
