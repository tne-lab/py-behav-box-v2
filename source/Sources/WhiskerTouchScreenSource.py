import socket
import threading

from Sources.Source import Source


class WhiskerTouchScreenSource(Source):

    def __init__(self, address='localhost', port=3233, display_num=0):
        super().__init__()
        try:
            self.display_num = display_num
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.client.connect((address, port))
            self.running = threading.Event()
            rt = threading.Thread(target=lambda: self.read())
            rt.start()
            self.client.send('DisplayClaim {}\n'.format(display_num).encode('utf-8'))
            self.client.send(b'DisplayEventCoords on\n')
            self.client.send('DisplayCreateDocument {}\n'.format(display_num).encode('utf-8'))
            self.client.send('DisplayShowDocument {} {}\n'.format(display_num, display_num).encode('utf-8'))
            self.vals = {}
        except:
            self.available = False

    def close_source(self) -> None:
        self.running.set()

    def read(self):
        while not self.running.is_set():
            msg = self.client.recv(4096).decode()
            if msg.startswith('Event:'):
                split_msg = msg[:-1].split(' ')
                self.vals[split_msg[1]][0] = not self.vals[split_msg[1]][0]
                self.vals[split_msg[1]][1] = [int(split_msg[2], int(split_msg[3]))]
        self.client.send(b'DisplayRelinquishAll\n')
        self.client.close()

    def register_component(self, _, component):
        self.components[component.id] = component
        self.vals[component.id] = (False, None)

    def read_component(self, component_id):
        return self.vals[component_id]

    def write_component(self, component_id, msg):
        if msg:
            self.client.send(
                'DisplayAddObject {} {} {};DisplaySetEvent {} {} TouchDown {};DisplaySetEvent {} {} TouchUp {}\n'.format(
                    self.display_num, self.display_num, component_id, self.display_num, component_id, component_id,
                    self.display_num, component_id, component_id
                ).encode('utf-8'))
        else:
            self.client.send('DisplayDeleteObject {} {}\n'.format(self.display_num, component_id).encode('utf-8'))

    def is_available(self):
        return self.available
