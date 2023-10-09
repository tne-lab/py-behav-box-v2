from __future__ import annotations
from typing import TYPE_CHECKING

import zmq
import json
from Sources.ThreadSource import ThreadSource

if TYPE_CHECKING:
    from Components.Component import Component
    from Tasks.Task import Task


class OESource(ThreadSource):
    def __init__(self, address, in_port, out_port):
        super(OESource, self).__init__()
        self.address = address
        self.in_port = in_port
        self.out_port = out_port
        self.context = None
        self.in_socket = None
        self.out_socket = None
        self.addresses = {}
        self.closing = False

    def initialize(self):
        try:
            self.context = zmq.Context()
            self.in_socket = self.context.socket(zmq.SUB)
            self.in_socket.connect("tcp://" + self.address + ":" + str(self.in_port))
            self.in_socket.setsockopt(zmq.SUBSCRIBE, b'ttl')

            self.out_socket = self.context.socket(zmq.REQ)
            self.out_socket.set(zmq.REQ_RELAXED, True)
            self.out_socket.connect("tcp://" + self.address + ":" + str(self.out_port))

            self.available = True

            while not self.closing:
                res = self.in_socket.poll(timeout=1000)
                if res != 0:
                    msg = self.in_socket.recv_multipart()
                    if len(msg) == 1:
                        envelope = msg
                    elif len(msg) == 2:
                        envelope, jsonStr = msg
                        jsonStr = json.loads(jsonStr.decode('utf-8'))
                        if jsonStr['type'] == 'ttl' and jsonStr['channel'] in self.addresses:
                            self.update_component(self.addresses[jsonStr['channel']], jsonStr)
            self.in_socket.close()
            self.out_socket.close()
        except:
            self.unavailable()

    def register_component(self, task: Task, component: Component) -> None:
        self.addresses[int(component.address) - 1] = component.id

    def close_source(self):
        self.closing = True

    def write_component(self, component_id, msg):
        if msg:
            self.out_socket.send(
                b"".join([b'TTL Channel=', str(self.components[component_id].address).encode('ascii'), b' on=1']))
            self.receive()
        else:
            self.out_socket.send(
                b"".join([b'TTL Channel=', str(self.components[component_id].address).encode('ascii'), b' on=0']))
            self.receive()

    def receive(self) -> None:
        try:
            self.out_socket.recv(flags=zmq.NOBLOCK)
        except zmq.ZMQError:
            pass
