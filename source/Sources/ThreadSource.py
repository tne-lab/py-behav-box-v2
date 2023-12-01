import threading
import traceback
from abc import ABC
from typing import List

import msgspec.msgpack

from Events import PybEvents
from Sources.Source import Source
import Utilities.Exceptions as pyberror


class ThreadSource(Source, ABC):

    def __init__(self):
        super(ThreadSource, self).__init__()
        self.run_thread = None
        self.run_stop = None

    def run(self):
        self.decoder = msgspec.msgpack.Decoder(type=List[PybEvents.subclass_union(PybEvents.PybEvent)])
        self.encoder = msgspec.msgpack.Encoder()
        try:
            self.run_stop = threading.Event()
            self.run_thread = threading.Thread(target=self.run_)
            self.run_thread.start()
            self.initialize()
        except pyberror.ComponentRegisterError as e:
            self.queue.send_bytes(self.encoder.encode(PybEvents.ErrorEvent(type(e).__name__, traceback.format_exc(), metadata={"sid": self.sid})))
            self.unavailable()
        except BaseException as e:
            self.queue.send_bytes(self.encoder.encode(PybEvents.ErrorEvent(type(e).__name__, traceback.format_exc(), metadata={"sid": self.sid})))
            self.unavailable()
            raise

    def run_(self):
        try:
            while True:
                events = self.decoder.decode(self.queue.recv_bytes())
                if not self.handle_events(events):
                    return
        except pyberror.ComponentRegisterError as e:
            self.queue.send_bytes(self.encoder.encode(PybEvents.ErrorEvent(type(e).__name__, traceback.format_exc(), metadata={"sid": self.sid})))
            self.unavailable()
        except BaseException as e:
            self.queue.send_bytes(self.encoder.encode(PybEvents.ErrorEvent(type(e).__name__, traceback.format_exc(), metadata={"sid": self.sid})))
            self.unavailable()
            raise
