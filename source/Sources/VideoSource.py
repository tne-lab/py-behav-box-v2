import asyncio
import os
from collections import deque
from datetime import datetime
import time
from multiprocessing import Process
from typing import Any

import cv2
import imutils
import qasync
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *

from Sources.Source import Source
from Utilities.PipeQueue import PipeQueue
from Utilities.create_task import create_task
from Utilities.handle_task_result import handle_task_result


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


class VideoProcess(Process):
    def __init__(self, inq, outq, screen_width, screen_height, rows, cols):
        super(VideoProcess, self).__init__()
        self.inq = inq
        self.outq = outq
        self.ml = None
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rows = rows
        self.cols = cols

        self.cameras = {}
        self.writers = {}
        self.fr = {}
        self.read_times = {}
        self.tasks = {}
        self.loop = None

    def run(self):
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

        if self.screen_width is None:
            self.screen_width = QApplication.desktop().screenGeometry().width()
        if self.screen_height is None:
            self.screen_height = QApplication.desktop().screenGeometry().height()
        mw.setGeometry(0, 0, self.screen_width, self.screen_height)
        mw.show()

        asyncio.set_event_loop(qasync.QEventLoop(app))
        self.loop = asyncio.get_event_loop()
        self.loop.run_in_executor(None, self.ipc_events)
        self.loop.run_forever()

    def ipc_events(self):
        while True:
            command = self.inq.get()
            if command["command"] == "StartFeed":
                task = asyncio.run_coroutine_threadsafe(self.start_feed(command), loop=self.loop)
                task.add_done_callback(handle_task_result)
            elif command["command"] == "StartRecord":
                task = asyncio.run_coroutine_threadsafe(self.start_record(command), loop=self.loop)
                task.add_done_callback(handle_task_result)
            elif command["command"] == "StopRecord":
                task = asyncio.run_coroutine_threadsafe(self.stop_record(command), loop=self.loop)
                task.add_done_callback(handle_task_result)
            elif command["command"] == "CloseComponent":
                task = asyncio.run_coroutine_threadsafe(self.close_component(command), loop=self.loop)
                task.add_done_callback(handle_task_result)

    async def start_feed(self, command):
        self.cameras[command["id"]] = CameraWidget(self.loop, self.screen_width // self.cols,
                                                   self.screen_height // self.rows,
                                                   command["address"])
        self.ml.addWidget(self.cameras[command["id"]].get_video_frame(), command["row"], command["col"], command["row_span"],
                          command["col_span"])
        self.fr[command["id"]] = command["fr"]

    async def start_record(self, command):
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # for AVI files
        self.writers[command["id"]] = cv2.VideoWriter(command["path"], fourcc, self.fr[command["id"]],
                                                      self.cameras[command["id"]].dims)
        self.read_times[command["id"]] = time.perf_counter()
        self.writers[command["id"]].write(self.cameras[command["id"]].deque[-1])
        self.tasks[command["id"]] = create_task(self.process_frames(command["id"]))

    async def stop_record(self, command):
        self.writers[command["id"]].release()
        self.tasks[command["id"]].cancel()
        del self.writers[command["id"]]
        del self.read_times[command["id"]]
        del self.tasks[command["id"]]

    async def close_component(self, command):
        if command["id"] in self.writers:
            await self.stop_record(command)
        await self.cameras[command["id"]].stop()
        self.ml.removeWidget(self.cameras[command["id"]].get_video_frame())
        self.cameras[command["id"]].get_video_frame().deleteLater()
        del self.cameras[command["id"]]
        del self.fr[command["id"]]

    async def process_frames(self, vid):
        while True:
            if vid in self.writers:
                while self.read_times[vid] + 1 / self.fr[vid] < time.perf_counter():
                    self.writers[vid].write(self.cameras[vid].deque[-1])
                    self.read_times[vid] += 1 / self.fr[vid]
            await asyncio.sleep(1 / self.fr[vid])


class VideoSource(Source):
    def __init__(self, screen_width=None, screen_height=None, rows=None, cols=None):
        super(VideoSource, self).__init__()
        self.available = True
        self.inq = PipeQueue()
        self.outq = PipeQueue()
        self.video_process = VideoProcess(self.outq, self.inq, eval(screen_width), eval(screen_height), eval(rows),
                                          eval(cols))
        self.video_process.start()

    async def register_component(self, task, component):
        await super().register_component(task, component)
        command = {"command": "StartFeed", "id": component.id, "address": component.address, "row": component.row,
                   "col": component.col, "row_span": component.row_span, "col_span": component.col_span,
                   "fr": component.fr}
        self.outq.put(command)

    def write_component(self, component_id: str, msg: Any) -> None:
        if msg:
            desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
            path = "{}\\py-behav\\{}\\Data\\{}\\{}\\".format(desktop, type(self.tasks[component_id]).__name__,
                                                             self.tasks[component_id].metadata["subject"],
                                                             datetime.now().strftime("%m-%d-%Y")) + self.components[component_id].name + ".avi"
            command = {"command": "StartRecord", "id": component_id, "path": path}
            self.outq.put(command)
        else:
            command = {"command": "StopRecord", "id": component_id}
            self.outq.put(command)

    def close_source(self):
        self.available = False

    def close_component(self, component_id: str) -> None:
        command = {"command": "CloseComponent", "id": component_id}
        self.outq.put(command)

    def is_available(self):
        return self.available
