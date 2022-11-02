from enum import Enum
from Tasks.Task import Task
from Components.Video import Video


class VideoSync(Task):
    """@DynamicAttrs"""

    class States(Enum):
        RECORDING = 0

    @staticmethod
    def get_components():
        return {
            'cam': [Video]
        }

    def init_state(self):
        return self.States.RECORDING

    def start(self):
        self.cam.start()

    def stop(self):
        self.cam.stop()

    def is_complete(self):
        return False
