from __future__ import annotations
from typing import TYPE_CHECKING

import zmq
import zmq.asyncio
import json
from Sources.Source import Source
from Utilities.create_task import create_task

if TYPE_CHECKING:
    from Components.Component import Component
    from Tasks.Task import Task


class OESource(Source):
    def __init__(self, address, in_port, out_port):
        super(OESource, self).__init__()
        try:
            self.context = zmq.asyncio.Context()
            self.in_socket = self.context.socket(zmq.SUB)
            self.in_socket.connect("tcp://" + address + ":" + str(in_port))
            self.in_socket.setsockopt(zmq.SUBSCRIBE, b'ttl')
            self.read_task = create_task(self.read())

            self.out_socket = self.context.socket(zmq.REQ)
            self.out_socket.set(zmq.REQ_RELAXED, True)
            self.out_socket.connect("tcp://" + address + ":" + str(out_port))

            self.available = True
        except:
            self.available = False
        self.addresses = {}

    async def register_component(self, task: Task, component: Component) -> None:
        await super().register_component(task, component)
        self.addresses[int(component.address) - 1] = component.id

    def close_source(self):
        self.read_task.cancel()
        self.in_socket.close()
        self.out_socket.close()

    async def read(self):
        while True:
            msg = await self.in_socket.recv_multipart()
            if len(msg) == 1:
                envelope = msg
            elif len(msg) == 2:
                envelope, jsonStr = msg
                jsonStr = json.loads(jsonStr.decode('utf-8'))
                if jsonStr['type'] == 'ttl' and jsonStr['channel'] in self.addresses:
                    self.update_component(self.addresses[jsonStr['channel']], jsonStr)

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

    def is_available(self):
        return self.available
