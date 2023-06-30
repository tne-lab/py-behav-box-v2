import asyncio
import time
from threading import Timer


class Timeout:
    def __init__(self, target):
        self.target = target
        self.task = None
        self.start_time = None
        self.started = False
        self.duration = 0
        self.elapsed_time = 0

    def start(self, duration):
        if not self.started:
            self.duration = duration
            self.task = Timer(duration, self.handler)
            self.task.start()
            self.start_time = time.perf_counter()
            self.started = True

    def pause(self):
        if self.started and self.start_time is not None:
            self.task.cancel()
            self.elapsed_time = time.perf_counter() - self.start_time
            self.start_time = None

    def stop(self):
        if self.started:
            self.task.cancel()
            self.elapsed_time = 0
            self.start_time = None
            self.started = False
            self.task = None

    def resume(self):
        if self.started and self.start_time is None:
            self.duration = self.time_remaining()
            self.task = Timer(self.duration, self.handler)
            self.task.start()
            self.start_time = time.perf_counter()

    def extend(self, duration):
        self.pause()
        self.start(self.time_remaining() + duration)

    def time_remaining(self):
        if self.start_time is not None:
            return self.duration - (time.perf_counter() - self.start_time)
        else:
            return self.duration - self.elapsed_time

    async def handler(self):
        self.elapsed_time = 0
        self.started = False
        self.start_time = None
        self.duration = 0
        self.elapsed_time = 0
        self.target()
        self.task = None
