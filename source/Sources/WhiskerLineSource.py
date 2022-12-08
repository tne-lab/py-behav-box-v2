import socket
import threading

from Components.Component import Component
from Sources.Source import Source


class WhiskerLineSource(Source):

    def __init__(self, address='localhost', port=3233):
        super(WhiskerLineSource, self).__init__()
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.client.connect((address, port))
            self.running = threading.Event()
            rt = threading.Thread(target=lambda: self.read())
            rt.start()
            self.vals = {}
        except:
            self.available = False

    def read(self):
        while not self.running.is_set():
            msg = self.client.recv(4096).decode()
            if msg.startswith('Event:'):
                self.vals[msg[:-1].split(' ')[1]] = not self.vals[msg[:-1].split(' ')[1]]
        self.client.send(b'LineRelinquishAll\n')
        self.client.close()

    def register_component(self, _, component):
        self.components[component.id] = component
        if component.get_type() == Component.Type.DIGITAL_INPUT:
            self.client.send(
                'LineClaim {} -ResetOff;LineSetEvent {} both {}\n'.format(component.address, component.address,
                                                                          component.id).encode('utf-8'))
            self.vals[component.id] = False
        else:
            self.client.send('LineClaim {} -ResetOff\n'.format(component.address).encode('utf-8'))

    def close_source(self):
        self.running.set()

    def read_component(self, component_id):
        return self.vals[component_id]

    def write_component(self, component_id, msg):
        if msg:
            self.client.send('LineSetState {} on\n'.format(self.components[component_id].address).encode('utf-8'))
        else:
            self.client.send('LineSetState {} off\n'.format(self.components[component_id].address).encode('utf-8'))

    def is_available(self):
        return self.available
