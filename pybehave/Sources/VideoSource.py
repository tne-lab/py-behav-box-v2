import asyncio
import concurrent.futures
import ctypes
import threading
from abc import ABC, abstractmethod
from asyncio import Future
import time
from typing import Any, Dict

import cv2
import imutils
import numpy as np
import qasync
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *

from pybehave.Components.Component import Component
from pybehave.Events import PybEvents
from pybehave.Sources.ThreadSource import ThreadSource
from pybehave.Sources.library.tisgrabber import tisgrabber


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
        self.frame = None

        self.dims = None

        self.loop = loop
        # Start background frame grabbing
        self.vp.start()
        # Periodically set video frame to display
        self.update_task = asyncio.run_coroutine_threadsafe(self.set_frame(), self.loop)

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
        self.app = None

    def initialize(self):
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

        if self.screen_width == 'None':
            self.screen_width = QApplication.desktop().screenGeometry().width()
        if self.screen_height == 'None':
            self.screen_height = QApplication.desktop().screenGeometry().height()
        self.screen_height = int(self.screen_height)
        self.screen_width = int(self.screen_width)
        mw.setGeometry(0, 0, self.screen_width, self.screen_height)
        mw.show()
        asyncio.set_event_loop(qasync.QEventLoop(self.app))
        self.loop = asyncio.get_event_loop()
        self.loop.run_forever()

    def register_component(self, component, metadata):
        asyncio.run_coroutine_threadsafe(self.register_component_async(component, metadata), loop=self.loop)

    async def register_component_async(self, component, metadata):
        if metadata["vid_type"] == "imaging_source":
            vp = ImagingSourceProvider(component.address)
        else:
            vp = WebcamProvider(component.address)
        self.cameras[component.id] = CameraWidget(self.loop, self.screen_width // self.cols, self.screen_height // self.rows, vp)
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
            self.writers[component_id].write(self.cameras[component_id].vp.get_frame())
            self.tasks[component_id] = asyncio.run_coroutine_threadsafe(self.process_frames(component_id), loop=self.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.stop_record(component_id), loop=self.loop)

    async def process_frames(self, vid):
        while True:
            if vid in self.writers:
                while self.read_times[vid] + 1 / self.fr[vid] < time.perf_counter():
                    self.writers[vid].write(self.cameras[vid].vp.get_frame())
                    self.read_times[vid] += 1 / self.fr[vid]
            await asyncio.sleep(1 / self.fr[vid])

    async def stop_record(self, component_id):
        self.tasks[component_id].cancel()
        self.writers[component_id].release()
        del self.writers[component_id]
        del self.read_times[component_id]
        del self.tasks[component_id]

    def close_source(self):
        futures = []
        for comp in self.components:
            futures.append(self.close_component(comp))
        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
        self.app.exit()

    def close_component(self, component_id: str) -> Future:
        return asyncio.run_coroutine_threadsafe(self.close_component_async(component_id), loop=self.loop)

    async def close_component_async(self, component_id):
        if component_id in self.writers:
            await self.stop_record(component_id)
        await self.cameras[component_id].stop()
        self.ml.removeWidget(self.cameras[component_id].get_video_frame())
        self.cameras[component_id].get_video_frame().deleteLater()
        del self.cameras[component_id]
        del self.fr[component_id]

    @staticmethod
    def metadata_defaults(comp_type: Component.Type = None) -> Dict:
        return {"fr": 30, "row": 0, "col": 0, "row_span": 0, "col_span": 0}


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
