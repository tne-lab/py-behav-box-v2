import queue
import time
from collections import OrderedDict
from queue import Queue
from threading import Thread


class Timeout:

    def __init__(self, name: str, chamber: int, duration: float, target, args):
        self.name = name
        self.chamber = str(chamber)
        self.duration = duration
        self.duration_ = self.duration
        self.target = target
        self.args = args
        self.start_time = None
        self.started = False
        self.elapsed_time = 0

    def start(self):
        self.started = True
        self.start_time = time.perf_counter()
        self.elapsed_time = 0

    def pause(self):
        self.elapsed_time = time.perf_counter() - self.start_time
        self.start_time = None

    def resume(self):
        self.duration_ = self.time_remaining()
        self.start_time = time.perf_counter()

    def reset(self, duration: float):
        self.duration = duration
        self.duration_ = self.duration
        self.start()

    def extend(self, duration: float):
        self.duration += duration
        self.duration_ += duration

    def time_remaining(self):
        if self.start_time is not None:
            return self.duration_ - (time.perf_counter() - self.start_time)
        else:
            return self.duration_ - self.elapsed_time

    def execute(self):
        self.target(*self.args)


class TimeoutManager(Thread):

    def __init__(self):
        super(TimeoutManager, self).__init__()
        self.timeouts = OrderedDict()
        self.timeout_queue = Queue()

    def run(self):
        while True:
            wait = None
            for timeout in self.timeouts.values():
                if wait is None:
                    wait = timeout.time_remaining()
                else:
                    wait = min(wait, timeout.time_remaining())

            try:

                event = self.timeout_queue.get(timeout=wait)

                if isinstance(event, Timeout):
                    self.timeouts[event.chamber + "/" + event.name] = event
                    event.start()

                if isinstance(event, tuple):
                    if event[0] == "Reset":
                        self.timeouts[event[1].chamber + "/" + event[1].name] = event[1]
                        self.timeouts[event[1].chamber + "/" + event[1].name].start()
                    elif event[0] == "Quit":
                        return
                    elif event[1] in self.timeouts:
                        if event[0] == "Cancel":
                            del self.timeouts[event[1]]
                        elif event[0] == "Pause":
                            self.timeouts[event[1]].pause()
                        elif event[0] == "Resume":
                            self.timeouts[event[1]].resume()
                        elif event[0] == "Extend":
                            self.timeouts[event[1]].extend(event[2])
            except queue.Empty:
                pass

            for name in list(self.timeouts.keys()):
                if self.timeouts[name].time_remaining() <= 0:
                    self.timeouts[name].execute()
                    del self.timeouts[name]

    def add_timeout(self, timeout: Timeout):
        self.timeout_queue.put(timeout)

    def cancel_timeout(self, name: str):
        self.timeout_queue.put(("Cancel", name))

    def pause_timeout(self, name: str):
        self.timeout_queue.put(("Pause", name))

    def resume_timeout(self, name: str):
        self.timeout_queue.put(("Resume", name))

    def reset_timeout(self, timeout: Timeout):
        self.timeout_queue.put(("Reset", timeout))

    def extend_timeout(self, name: str, duration: float):
        self.timeout_queue.put(("Extend", name, duration))

    def quit(self):
        self.timeout_queue.put(("Quit", None))
