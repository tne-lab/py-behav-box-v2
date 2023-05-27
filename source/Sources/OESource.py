import threading
import time

import zmq
import json

from zmq import ZMQError

from Sources.Source import Source


class OESource(Source):

    def __init__(self, address, port, delay=0):
        super(OESource, self).__init__()
        try:
            context = zmq.Context()
            self.socket = context.socket(zmq.SUB)
            self.socket.connect("tcp://" + address + ":" + str(port))
            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLIN)
            self.delay = int(delay)
            self.socket.setsockopt(zmq.SUBSCRIBE, b'ttl')
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
        self.socket.close()

    def clear_thread(self):
        while ~self.stop_event.is_set():
            if time.perf_counter() - self.last_read > 5:
                sockets = self.poller.poll(self.delay)
                for socket in sockets:
                    try:
                        while True:
                            socket[0].recv_multipart(flags=zmq.NOBLOCK)
                    except ZMQError:
                        pass
                self.last_read = time.perf_counter()
            time.sleep(5)

    def read_component(self, component_id):
        self.last_read = time.perf_counter()
        sockets = self.poller.poll(self.delay)
        jsonStrs = []
        for socket in sockets:
            try:
                while True:
                    msg = socket[0].recv_multipart(flags=zmq.NOBLOCK)
                    if len(msg) == 1:
                        envelope = msg
                    elif len(msg) == 2:
                        envelope, jsonStr = msg
                        jsonStr = json.loads(jsonStr.decode('utf-8'))
                        if jsonStr['type'] == 'ttl' and jsonStr['channel'] == int(
                                self.components[component_id].address) - 1:
                            jsonStrs.append(jsonStr)
            except ZMQError:
                pass
        return jsonStrs

    def write_component(self, component_id, msg):
        pass

    def is_available(self):
        return self.available
