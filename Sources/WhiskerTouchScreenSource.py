import threading
from queue import Queue

from Sources.Source import Source

import time
from twisted.internet import reactor
from whisker.api import (
    Pen,
    PenStyle,
    BrushStyle,
    BrushHatchStyle,
    Brush,
    Rectangle,
    DocEventType,
)
from whisker.constants import DEFAULT_PORT
from whisker.twistedclient import WhiskerTwistedTask

DEFAULT_DISPLAY_NUM = 0
DISPLAY = "display"
DOC = "doc"
AUDIO = "audio"


class WhiskerTouchScreenSource(Source, WhiskerTwistedTask):

    def __init__(self, display_num=DEFAULT_DISPLAY_NUM, port=DEFAULT_PORT):
        super().__init__()
        self.display_size = None
        self.display_num = display_num
        self.port = port
        self.brush1 = Brush(
            colour=(0, 0, 0), bg_colour=(0, 255, 0),
            opaque=False)  # BLACK BACKGROUND
        self.brush2 = Brush(
            colour=(5, 5, 5), bg_colour=(0, 255, 0),
            opaque=False)  # Gray dead zone to prevent tail touches
        self.pen = Pen(width=3, colour=(0, 0, 0), style=PenStyle.solid)
        self.brush = Brush(
            colour=(255, 0, 0), bg_colour=(0, 255, 0),
            opaque=True, style=BrushStyle.hatched,
            hatch_style=BrushHatchStyle.bdiagonal)  #
        self.background_ht = 0
        self.dead_zone_ht = 1
        self.pics = []
        self.coords = []
        self.dims = []
        self.back_q = Queue()
        self.q = Queue()
        whiskerThread = threading.Thread(target=self.main, args=[], kwargs=None)
        whiskerThread.daemon = True
        whiskerThread.start()
        time.sleep(1)

    def fully_connected(self) -> None:  # RUNS ONCE WHEN FULLY CONNECTED
        """
        Called when the server is fully connected. Sets up the "task".
        """
        print("FULLY CONNECTED")
        self.whisker.report_name("Whisker Twisted Client for touchscreen Task")
        self.whisker.timestamps(True)
        # BP
        self.whisker.claim_display(number=self.display_num, alias=DISPLAY)
        # self.whisker.set_media_directory(self.media_dir)
        self.display_size = self.whisker.display_get_size(DISPLAY)
        print('display size:', self.display_size)
        self.whisker.display_event_coords(True)

        self.whisker.display_scale_documents(DISPLAY, True)
        self.whisker.display_blank(DISPLAY)

    def draw(self):
        '''
        Draws current pics stored in self.pics, background and stop button
        Also creates events corresponding to all
        '''
        # Display stuff on screen
        # Create a new document everytime we draw a new screen. (otherwise we might be drawing stuff on top of eachother.. seems bad)
        self.whisker.display_create_document(DOC)
        self.whisker.display_show_document(DISPLAY, DOC)
        with self.whisker.display_cache_wrapper(DOC):
            # Draw background
            # Lock out bottom 100 pixels of display to minimize tail Touches
            self.background_ht = self.display_size[1] - self.dead_zone_ht
            self.whisker.display_add_obj_rectangle(DOC, "background",
                                                   Rectangle(left=0, top=0, width=self.display_size[0],
                                                             height=self.background_ht),
                                                   self.pen, self.brush1)

            # Draw dead zone at bottom of screen.
            # Lock out bottom 100 pixels of display to minimize tail Touches
            self.whisker.display_add_obj_rectangle(DOC, "background",
                                                   Rectangle(left=0, top=self.background_ht, width=self.display_size[0],
                                                             height=self.dead_zone_ht),
                                                   self.pen, self.brush2)

            # Draw pictures
            for i in range(0, len(self.pics)):
                bit = self.whisker.display_add_obj_bitmap(
                    DOC, "picture" + str(i), self.coords[i], filename=self.pics[i],
                    stretch=True, height=self.dims[i][0], width=self.dims[i][1])  # Returns T or F
                if not bit:
                    pass
            self.whisker.display_send_to_back(DOC, "background")
            self.setEvents()

    # Handle creation/deletion of picture Events
    def setEvents(self):
        # Set events for all pictures
        for i in range(0, len(self.pics)):
            self.whisker.display_set_event(DOC, "picture" + str(i), self.pics[i], DocEventType.touch_down)
        # Set event for background and end of task
        self.whisker.display_set_event(DOC, "background", "missedClick", DocEventType.touch_down)
        self.whisker.timer_set_event("checkZMQ", 5, -1)

    def clearEvents(self):
        # Clears events and DOC for all pictures to get ready for new ones
        for i in range(0, len(self.pics)):
            self.whisker.display_clear_event(DOC, "picture" + str(i))
        self.whisker.display_clear_event(DOC, "background")
        self.whisker.timer_clear_event("checkZMQ")
        self.whisker.display_delete_document(DOC)

    def incoming_event(self, event: str, timestamp: int = None) -> None:
        """
        Responds to incoming events from Whisker.
        """
        if not event == "checkZMQ":
            event, x, y = event.split(' ')
            self.back_q.put((int(x), int(y)))

    def register_component(self, _):
        pass

    def main(self):
        self.connect('localhost', self.port)
        while True:
            try:
                reactor.run()  # starts Twisted and thus network processing
                break
            except:
                print('trying to start touchscreen, if stuck check whiskerTouch main')

    def close_source(self):
        pass

    def read_component(self, component_id):
        touches = []
        while not self.back_q.empty():
            touches.append(self.back_q.get())
        return touches

    def write_component(self, component_id, msg):
        self.clearEvents()
        self.pics = []
        self.coords = []
        self.dims = []
        for path in msg.keys():
            self.pics.append(path)
            self.coords.append(msg[path]["coords"])
            self.dims.append(msg[path]["dim"])
        self.draw()
