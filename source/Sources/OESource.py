import threading
import time
import zmq
import json
from zmq import ZMQError
from Sources.Source import Source


class OESource(Source):
    def __init__(self, address, in_port, out_port, delay=0):
        super(OESource, self).__init__()
        try:
            self.context = zmq.Context()
            self.in_socket = self.context.socket(zmq.SUB)
            self.in_socket.connect("tcp://" + address + ":" + str(in_port))
            self.poller = zmq.Poller()
            self.poller.register(self.in_socket, zmq.POLLIN)
            self.delay = int(delay)
            self.in_socket.setsockopt(zmq.SUBSCRIBE, b'ttl')

            self.out_socket = self.context.socket(zmq.REQ)
            self.out_socket.set(zmq.REQ_RELAXED, True)
            self.out_socket.connect("tcp://" + address + ":" + str(out_port))

            self.available = True
            self.last_read = time.perf_counter()
            self.thread = threading.Thread(target=self.clear_thread)
            self.stop_event = threading.Event()
            self.thread.start()
        except:
            self.available = False

    def register_component(self, _, component):
        self.components[component.id] = component

    def close_source(self):
        self.stop_event.set()
        self.thread.join()
        self.in_socket.close()
        self.out_socket.close()
        self.context.close()

    def clear_thread(self):
        while not self.stop_event.is_set():
            if time.perf_counter() - self.last_read > 1:
                sockets = self.poller.poll(self.delay)
                for socket in sockets:
                    try:
                        while True:
                            socket[0].recv_multipart(flags=zmq.NOBLOCK)
                    except ZMQError:
                        pass
                self.last_read = time.perf_counter()
            self.stop_event.wait(5)
        print("cleared")

    def read_component(self, component_id):
        self.last_read = time.perf_counter()
        sockets = self.poller.poll(self.delay)
        jsonStrs = []
        for socket in sockets:
            msg = socket[0].recv_multipart()
            if len(msg) == 1:
                envelope = msg
            elif len(msg) == 2:
                envelope, jsonStr = msg
                jsonStr = json.loads(jsonStr.decode('utf-8'))
                if jsonStr['type'] == 'ttl' and jsonStr['channel'] == int(
                        self.components[component_id].address) - 1:
                    jsonStrs.append(jsonStr)
        return jsonStrs

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
