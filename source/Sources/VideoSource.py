import asyncio
from collections import deque
import time
from typing import Any

import cv2
import imutils
import qasync
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *

from Events import PybEvents
from Sources.ThreadSource import ThreadSource


class CameraWidget(QWidget):
    """Independent camera feed
    Uses threading to grab IP camera frames in the background

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param stream_link - IP/RTSP/Webcam link
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, loop, width, height, src=0, aspect_ratio=False, parent=None, deque_size=1):
        super(CameraWidget, self).__init__(parent)
        # Initialize deque used to store frames read from the stream
        self.deque = deque(maxlen=deque_size)

        # Slight offset is needed since PyQt layouts have a built in padding
        # So add offset to counter the padding
        self.offset = 16
        self.screen_width = width - self.offset
        self.screen_height = height - self.offset
        self.maintain_aspect_ratio = aspect_ratio

        self.src = src

        # Flag to check if camera is valid/working
        self.online = True
        self.video_frame = QLabel()

        self.capture = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
        self.dims = None

        self.loop = loop
        # Start background frame grabbing
        self.get_frame_thread = asyncio.to_thread(self.get_frame)
        asyncio.ensure_future(self.get_frame_thread, loop=self.loop)
        # Periodically set video frame to display
        self.stop_event = asyncio.Event()
        self.update_task = asyncio.ensure_future(self.set_frame(), loop=self.loop)
        self.stopping = False

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""

        while True:
            try:
                if self.stopping:
                    self.loop.call_soon_threadsafe(self.stop_event.set)
                    return
                if self.capture.isOpened() and self.online:
                    # Read next frame from stream and insert into deque
                    status, frame = self.capture.read()
                    self.dims = (int(self.capture.get(3)), int(self.capture.get(4)))
                    if status:
                        self.deque.append(frame)
                    else:
                        self.capture.release()
                        self.online = False
            except AttributeError:
                pass

    async def set_frame(self):
        while True:
            await asyncio.sleep(1 / 30)
            """Sets pixmap image to video frame"""
            if self.deque and self.online:
                # Grab latest frame
                frame = self.deque[-1]

                # Keep frame aspect ratio
                if self.maintain_aspect_ratio:
                    self.frame = imutils.resize(frame, width=self.screen_width)
                # Force resize
                else:
                    self.frame = cv2.resize(frame, (self.screen_width, self.screen_height))

                # Add timestamp to cameras
                # cv2.rectangle(self.frame, (self.screen_width - 190, 0), (self.screen_width, 50), color=(0, 0, 0),
                #               thickness=-1)
                # cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.screen_width - 185, 37),
                #             cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), lineType=cv2.LINE_AA)

                # Convert to pixmap and set to video frame
                img = QImage(self.frame, self.frame.shape[1], self.frame.shape[0],
                             QImage.Format_RGB888).rgbSwapped()
                pix = QPixmap.fromImage(img)
                self.video_frame.setPixmap(pix)

    async def stop(self):
        self.stopping = True
        self.update_task.cancel()
        await self.stop_event.wait()
        self.capture.release()

    def get_video_frame(self):
        return self.video_frame


class VideoSource(ThreadSource):
    def __init__(self, screen_width=None, screen_height=None, rows=None, cols=None):
        super(VideoSource, self).__init__()
        self.available = True
        self.out_paths = {}
        self.ml = None
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rows = int(rows)
        self.cols = int(cols)
        self.cameras = {}
        self.writers = {}
        self.fr = {}
        self.read_times = {}
        self.tasks = {}
        self.loop = None

    def initialize(self):
        app = QApplication([])
        # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt())
        app.setStyle(QStyleFactory.create("Cleanlooks"))
        mw = QMainWindow()
        mw.setWindowTitle('Camera GUI')
        # mw.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        cw = QWidget()
        self.ml = QGridLayout()
        cw.setLayout(self.ml)
        mw.setCentralWidget(cw)

        if self.screen_width == 'None':
            self.screen_width = QApplication.desktop().screenGeometry().width()
        if self.screen_height == 'None':
            self.screen_height = QApplication.desktop().screenGeometry().height()
        self.screen_height = int(self.screen_height)
        self.screen_width = int(self.screen_width)
        mw.setGeometry(0, 0, self.screen_width, self.screen_height)
        mw.show()
        asyncio.set_event_loop(qasync.QEventLoop(app))
        self.loop = asyncio.get_event_loop()
        self.loop.run_forever()

    def register_component(self, component, metadata):
        asyncio.run_coroutine_threadsafe(self.register_component_async(component, metadata), loop=self.loop)

    async def register_component_async(self, component, metadata):
        self.cameras[component.id] = CameraWidget(self.loop, self.screen_width // self.cols, self.screen_height // self.rows,
                                                  int(component.address))
        self.ml.addWidget(self.cameras[component.id].get_video_frame(), metadata["row"], metadata["col"],
                          metadata["row_span"], metadata["col_span"])
        self.fr[component.id] = metadata["fr"]

    def output_file_changed(self, event: PybEvents.OutputFileChangedEvent) -> None:
        for cid, chamber in self.component_chambers.items():
            if chamber == event.chamber:
                self.out_paths[cid] = event.output_file

    def write_component(self, component_id: str, msg: Any) -> None:
        if msg:
            if self.components[component_id].name is None:
                path = self.out_paths[component_id] + str(time.time()) + ".avi"
            else:
                path = self.out_paths[component_id] + self.components[component_id].name + ".avi"
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # for AVI files
            self.writers[component_id] = cv2.VideoWriter(path, fourcc, self.fr[component_id],
                                                         self.cameras[component_id].dims)
            self.read_times[component_id] = time.perf_counter()
            self.writers[component_id].write(self.cameras[component_id].deque[-1])
            self.tasks[component_id] = asyncio.run_coroutine_threadsafe(self.process_frames(component_id), loop=self.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.stop_record(component_id), loop=self.loop)

    async def process_frames(self, vid):
        while True:
            if vid in self.writers:
                while self.read_times[vid] + 1 / self.fr[vid] < time.perf_counter():
                    self.writers[vid].write(self.cameras[vid].deque[-1])
                    self.read_times[vid] += 1 / self.fr[vid]
            await asyncio.sleep(1 / self.fr[vid])

    async def stop_record(self, component_id):
        self.tasks[component_id].cancel()
        self.writers[component_id].release()
        del self.writers[component_id]
        del self.read_times[component_id]
        del self.tasks[component_id]

    def close_source(self):
        self.available = False

    def close_component(self, component_id: str) -> None:
        asyncio.run_coroutine_threadsafe(self.close_component_async(component_id), loop=self.loop)

    async def close_component_async(self, component_id):
        if component_id in self.writers:
            await self.stop_record(component_id)
        self.cameras[component_id].stop()
        self.ml.removeWidget(self.cameras[component_id].get_video_frame())
        self.cameras[component_id].get_video_frame().deleteLater()
        del self.cameras[component_id]
        del self.fr[component_id]
