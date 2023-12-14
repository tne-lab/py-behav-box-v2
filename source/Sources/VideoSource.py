import asyncio
import ctypes
import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime
import time
from multiprocessing import Process
from typing import Any

import cv2
import imutils
import numpy as np
import qasync
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *

from Sources.Source import Source
from Sources.library.tisgrabber import tisgrabber
from Utilities.PipeQueue import PipeQueue
from Utilities.create_task import create_task
from Utilities.handle_task_result import handle_task_result


class VideoProvider(ABC):

    @abstractmethod
    def get_frame(self):
        raise NotImplementedError

    @abstractmethod
    def start(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    @abstractmethod
    def isOpened(self):
        raise NotImplementedError

    @abstractmethod
    def release(self):
        raise NotImplementedError


class CameraWidget(QWidget):
    """Independent camera feed
    Uses threading to grab IP camera frames in the background

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param stream_link - IP/RTSP/Webcam link
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, loop, width, height, vp: VideoProvider, aspect_ratio=False, parent=None):
        super(CameraWidget, self).__init__(parent)

        # Slight offset is needed since PyQt layouts have a built in padding
        # So add offset to counter the padding
        self.offset = 16
        self.screen_width = width - self.offset
        self.screen_height = height - self.offset
        self.maintain_aspect_ratio = aspect_ratio

        self.vp = vp

        # Flag to check if camera is valid/working
        self.video_frame = QLabel()

        self.dims = None

        self.loop = loop
        # Start background frame grabbing
        self.vp.start()
        # Periodically set video frame to display
        self.update_task = asyncio.create_task(self.set_frame())
        self.update_task.add_done_callback(handle_task_result)

    async def set_frame(self):
        while True:
            await asyncio.sleep(1 / 30)
            """Sets pixmap image to video frame"""
            frame = self.vp.get_frame()
            if frame is not None:
                self.dims = (frame.shape[1], frame.shape[0])
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
        self.update_task.cancel()
        self.vp.release()

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
        self.app = None

    def run(self):
        self.app = QApplication([])
        # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt())
        self.app.setStyle(QStyleFactory.create("Cleanlooks"))
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

        asyncio.set_event_loop(qasync.QEventLoop(self.app))
        self.loop = asyncio.get_event_loop()
        task = self.loop.run_in_executor(None, self.ipc_events)
        task.add_done_callback(handle_task_result)
        self.loop.run_forever()

    def ipc_events(self):
        while True:
            available = self.inq.poll(1)
            if available:
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
        if command["vid_type"] == "imaging_source":
            vp = ImagingSourceProvider(command["address"])
        else:
            vp = WebcamProvider(command["address"])
        self.cameras[command["id"]] = CameraWidget(self.loop, self.screen_width // self.cols,
                                                   self.screen_height // self.rows, vp)
        self.ml.addWidget(self.cameras[command["id"]].get_video_frame(), command["row"], command["col"], command["row_span"],
                          command["col_span"])
        self.fr[command["id"]] = command["fr"]

    async def start_record(self, command):
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # for AVI files
        self.writers[command["id"]] = cv2.VideoWriter(command["path"], fourcc, self.fr[command["id"]],
                                                      self.cameras[command["id"]].dims)
        self.read_times[command["id"]] = time.perf_counter()
        self.writers[command["id"]].write(self.cameras[command["id"]].vp.get_frame())
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
                    self.writers[vid].write(self.cameras[vid].vp.get_frame())
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
                   "col": component.col, "row_span": component.row_span if hasattr(component, "row_span") else 1,
                   "col_span": component.col_span if hasattr(component, "col_span") else 1,
                   "fr": component.fr, "vid_type": component.vid_type if hasattr(component, "vid_type") else "webcam"}
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


class WebcamProvider(VideoProvider):

    def __init__(self, src):
        super(WebcamProvider, self).__init__()
        self.stream = cv2.VideoCapture(int(src), cv2.CAP_DSHOW)
        (self.grabbed, self.frame) = self.stream.read()
        self.dims = (int(self.stream.get(3)), int(self.stream.get(4)))
        self.stopped = False

    def get_frame(self):
        return self.frame

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


class ImagingSourceProvider(VideoProvider):

    class CallbackData(ctypes.Structure):
        """ Example for user data passed to the callback function. """

        def __init__(self):
            self.cvMat = None

    def callback(self, hGrabber, pBuffer, framenumber, pData):
        """ This is an example callback function for image processing with
            opencv. The image data in pBuffer is converted into a cv Matrix
            and with cv.mean() the average brightness of the image is
            measuered.

        :param: hGrabber: This is the real pointer to the grabber object.
        :param: pBuffer : Pointer to the first pixel's first byte
        :param: framenumber : Number of the frame since the stream started
        :param: pData : Pointer to additional user data structure
        """
        # print("camera {}". format(pData.index))
        Width = ctypes.c_long()
        Height = ctypes.c_long()
        BitsPerPixel = ctypes.c_int()
        colorformat = ctypes.c_int()

        # Query the image description values
        self.ic.IC_GetImageDescription(hGrabber, Width, Height, BitsPerPixel, colorformat)

        # Calculate the buffer size
        bpp = int(BitsPerPixel.value / 8.0)
        buffer_size = Width.value * Height.value * bpp

        if buffer_size > 0:
            image = ctypes.cast(pBuffer,
                                ctypes.POINTER(
                                    ctypes.c_ubyte * buffer_size))

            self.frame = np.ndarray(buffer=image.contents,
                                     dtype=np.uint8,
                                     shape=(Height.value,
                                            Width.value,
                                            bpp))

    def __init__(self, src):
        self.ic = ctypes.cdll.LoadLibrary("./Sources/library/tisgrabber/tisgrabber_x64.dll")
        tisgrabber.declareFunctions(self.ic)
        self.ic.IC_InitLibrary(0)
        self.camera = self.ic.IC_CreateGrabber()
        self.ic.IC_OpenDevByUniqueName(self.camera, tisgrabber.T(src))
        self.data = self.CallbackData()
        self.frame = None
        self.Callbackfuncptr = self.ic.FRAMEREADYCALLBACK(self.callback)

    def get_frame(self):
        return self.frame

    def start(self):
        if self.ic.IC_IsDevValid(self.camera):
            self.ic.IC_SetFrameReadyCallback(self.camera, self.Callbackfuncptr, self.data)
            self.ic.IC_SetContinuousMode(self.camera, 0)
            self.ic.IC_StartLive(self.camera, 0)

    def stop(self):
        if self.ic.IC_IsDevValid(self.camera):
            self.ic.IC_StopLive(self.camera)

    def isOpened(self):
        return self.ic.IC_IsDevValid(self.camera)

    def release(self):
        if self.ic.IC_IsDevValid(self.camera):
            self.ic.IC_ReleaseGrabber(self.camera)
