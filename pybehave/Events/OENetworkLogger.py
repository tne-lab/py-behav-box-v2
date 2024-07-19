from __future__ import annotations

from pybehave.Events import PybEvents

try:
    import zmq
except ModuleNotFoundError:
    from pybehave.Utilities.Exceptions import MissingExtraError
    raise MissingExtraError('oe')

import collections
import threading
from typing import TYPE_CHECKING

from pybehave.Events.EventLogger import EventLogger

if TYPE_CHECKING:
    from pybehave.Events.LoggerEvent import LoggerEvent

import time


class OENetworkLogger(EventLogger):

    # Can use a CustomEvent: OEEvent
    # OEEvent expects a 'message_type' field in the metadata

    def __init__(self, name: str, address: str, port: str):
        super().__init__(name)
        context = zmq.Context()
        self.fd = None
        self.event_count = 0
        self.socket = context.socket(zmq.REQ)
        self.socket.set(zmq.REQ_RELAXED, True)
        self.socket.connect("tcp://" + address + ":" + str(port))

    def send_ttl_event(self, ec: int, ttl_type: str | float) -> None:
        if ttl_type == 'on':
            self.socket.send(
                b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=1']))
            self.receive()
        elif ttl_type == 'off':
            self.socket.send(
                b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=0']))
            self.receive()
        else:
            t = threading.Thread(target=self.send_ttl_event_, args=[ec, ttl_type])
            t.start()

    def send_ttl_event_(self, ec: int, dur: float) -> None:
        # Activate the TTL channels according to the bit sequence
        self.socket.send(
            b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=1']))
        self.receive()
        time.sleep(dur)
        self.socket.send(
            b"".join([b'TTL Channel=', str(ec).encode('ascii'), b' on=0']))
        self.receive()

    def send_string(self, msg: str) -> None:
        self.socket.send(msg.encode("utf-8"))
        self.receive()

    def receive(self) -> None:
        try:
            self.socket.recv(flags=zmq.NOBLOCK)
        except zmq.ZMQError:
            pass

    def log_events(self, events: collections.deque[LoggerEvent]) -> None:
        for event in events:
            self.event_count += 1
            if isinstance(event.event, PybEvents.CustomEvent) and event.event.event_type == 'OEEvent':
                if event.event.metadata['message_type'] == 'startAcquisition':
                    self.send_string("startAcquisition")
                elif event.event.metadata['message_type'] == 'stopAcquisition':
                    self.send_string("stopAcquisition")
                elif event.event.metadata['message_type'] == 'startRecord':
                    send_string = 'startRecord'
                    if "rec_dir" in event.event.metadata:
                        send_string += " RecDir=" + event.event.metadata['rec_dir']
                    if "prependText" in event.event.metadata:
                        send_string += " prependText=" + event.event.metadata['prependText']
                    if "appendText" in event.event.metadata:
                        send_string += " appendText=" + event.event.metadata['appendText']
                    self.send_string(send_string)
                elif event.event.metadata['message_type'] == 'stopRecord':
                    self.send_string("stopRecord")
            else:
                self.send_string(self.format_event(event, type(event.event).__name__))

    def close(self) -> None:
        self.socket.close()
