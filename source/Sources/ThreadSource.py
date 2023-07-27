import threading
from abc import ABC
from typing import List

import msgspec.msgpack

from Events import PybEvents
from Sources.Source import Source


class ThreadSource(Source, ABC):

    def __init__(self):
        super(ThreadSource, self).__init__()
        self.run_thread = None
        self.run_stop = None

    def run(self):
        self.run_stop = threading.Event()
        self.run_thread = threading.Thread(target=self.run_)
        self.run_thread.start()
        self.initialize()

    def run_(self):
        self.decoder = msgspec.msgpack.Decoder(type=List[PybEvents.subclass_union(PybEvents.PybEvent)])
        self.encoder = msgspec.msgpack.Encoder()
        while not self.run_stop.is_set():
            events = self.decoder.decode(self.queue.recv_bytes())
            self.handle_events(events)

    def close_source(self) -> None:
        self.run_stop.set()
        self.run_thread.join()