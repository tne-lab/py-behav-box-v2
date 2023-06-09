import threading
import time


class TimeoutThread:
    def __init__(self, target):
        self.target = target
        self.thread = None
        self.start_time = None
        self.started = False
        self.duration = 0
        self.elapsed_time = 0

    def start(self, duration):
        if not self.started:
            self.thread = threading.Timer(duration, self.handler)
            self.thread.start()
            self.start_time = time.perf_counter()
            self.started = True
            self.elapsed_time = 0
            self.duration = duration

    def pause(self):
        if self.started and self.start_time is not None:
            self.thread.cancel()
            self.elapsed_time = time.perf_counter() - self.start_time
            self.start_time = None

    def stop(self):
        if self.started:
            self.thread.cancel()
            self.elapsed_time = 0
            self.start_time = None
            self.started = False

    def resume(self):
        if self.started and self.start_time is None:
            new_duration = self.time_remaining()
            self.thread = threading.Timer(new_duration, self.handler)
            self.thread.start()
            self.start_time = time.perf_counter()
            self.elapsed_time = 0
            self.duration = new_duration

    def extend(self, duration):
        self.pause()
        self.start(self.time_remaining() + duration)

    def time_remaining(self):
        if self.start_time is not None:
            return self.duration - (time.perf_counter() - self.start_time)
        else:
            return self.duration - self.elapsed_time

    def handler(self):
        self.started = False
        self.start_time = None
        self.duration = 0
        self.elapsed_time = 0
        self.target()
        self.thread = None
