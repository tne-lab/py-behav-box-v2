import multiprocessing
import os
import pickle
import queue
import threading
import time
from multiprocessing import Process, Queue

import msgspec.msgpack
import psutil
import wres

from Events.PybEvents import ComponentUpdateEvent, HeartbeatEvent
from Tasks.TimeoutManager import TimeoutManager
import win_precise_time as wpt


def f(pipe, n, event):
    p = psutil.Process(os.getpid())
    p.nice(psutil.REALTIME_PRIORITY_CLASS)
    event.set()
    for i in range(n):
        # decode(read.recv_bytes())
        pipe.recv_bytes()
        # write.send(ComponentUpdateEvent(0, "test-0-0", True, {"test": "test", "test2": "test"}))
        # t = time.perf_counter()
        pipe.send_bytes(msgspec.msgpack.encode(ComponentUpdateEvent(0, "test-0-0", True, {"test": "test", "test2": "test"})))
        # print(time.perf_counter() - t)


def main():
    # p = psutil.Process(os.getpid())
    # p.nice(psutil.REALTIME_PRIORITY_CLASS)
    # tm = TimeoutManager()
    # tm.start()
    # p1, p2 = multiprocessing.Pipe()
    # event = multiprocessing.Event()
    # n = 100
    # p = Process(target=f, args=(p2, n, event))
    # p.start()
    # event.wait()
    # #t = time.perf_counter()
    # for i in range(n):
    #     # write.send(ComponentUpdateEvent(0, "test-0-0", True, {"test": "test", "test2": "test"}))
    #     t = time.perf_counter()
    #     p1.send_bytes(msgspec.msgpack.encode(HeartbeatEvent()))
    #     print(time.perf_counter() - t)
    #     # decode(read.recv_bytes())
    #     p1.recv_bytes()
    # #print((time.perf_counter() - t) / n)
    # # for i in range(10):
    # #     tm.add_timeout(Timeout(str(i), (i+1) / 10, lambda x: print(time.perf_counter() - x), time.perf_counter()))
    q = queue.Queue()
    for i in range(100):
        t = time.perf_counter()
        wpt.sleep(0.001)
        print(time.perf_counter() - t)


if __name__ == '__main__':
    main()
