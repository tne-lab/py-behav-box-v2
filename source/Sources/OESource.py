import zmq
import json
from source.Components.Component import Component
from Sources.Source import Source


class OESource(Source):

    def __init__(self, address, port, delay=1):
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://" + address + ":" + str(port))
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.delay = int(delay)
        self.socket.setsockopt(zmq.SUBSCRIBE, b'ttl')
        self.components = {}

    def register_component(self, _, component):
        self.components[component.id] = component

    def close_source(self):
        pass

    def read_component(self, component_id):
        sockets = self.poller.poll(self.delay)
        jsonStrs = []
        for socket in sockets:
            msg = socket[0].recv_multipart()
            if len(msg) == 1:
                envelope = msg
            elif len(msg) == 2:
                envelope, jsonStr = msg
                jsonStr = json.loads(jsonStr.decode('utf-8'))
                if jsonStr['type'] == 'ttl' and jsonStr['channel'] == int(self.components[component_id].address)-1:
                    jsonStrs.append(jsonStr)
        return jsonStrs

    def write_component(self, component_id, msg):
        # What do enable and send pulse do?
        pass
