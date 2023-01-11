import socket
import threading
import time
import traceback

import zmq

from Sources.Source import Source

from Components.Component import Component

from Utilities.Exceptions import ComponentRegisterError


class OSControllerSource(Source):

    def __init__(self, address='localhost', port=9296):
        super(OSControllerSource, self).__init__()
        try:
            context = zmq.Context.instance()
            self.client = context.socket(zmq.DEALER)
            self.client.connect("ipc://oscar.ipc")
            poll = zmq.Poller()
            poll.register(self.client, zmq.POLLIN)
            self.client.send(b"READY")
            sockets = dict(poll.poll(1000))
            if sockets:
                self.address, _, _ = socket.recv_multipart()
                self.available = True
                self.last_read = 0
                self.closing = False
            else:
                self.available = False
            #clear_thread = threading.Thread(target=lambda: self.clear())
            #clear_thread.start()
        except:
            traceback.print_exc()
            self.available = False
        self.components = {}
        self.input_ids = {}
        self.values = {}
        self.buffer = ""

    def clear(self):
        while not self.closing:
            if time.perf_counter() - self.last_read > 0.25:
                while True:
                    try:
                        msg = self.client.recv(4096).decode()
                        if len(msg) < 1024:
                            break
                    except BlockingIOError:
                        break
            time.sleep(0.25)

    def register_component(self, _, component):
        self.components[component.id] = component
        if "A" in component.address:
            parts = component.address.split('_')
            if component.get_type() == Component.Type.DIGITAL_OUTPUT:
                tp = 1
            elif component.get_type() == Component.Type.DIGITAL_INPUT:
                tp = 2
            elif component.get_type() == Component.Type.ANALOG_INPUT:
                tp = 3
            else:
                raise ComponentRegisterError
            self.client.send_multipart(self.address, b"", 'RegGPIO {} {} {}\n'.format(parts[0], parts[1], tp).encode('utf-8'))
        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.DIGITAL_OUTPUT:
            self.values[component.id] = False
        else:
            self.values[component.id] = 0

        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.ANALOG_INPUT:
            self.input_ids[component.address] = component.id

    def close_source(self):
        self.closing = True
        coms = []
        for component in self.components:
            parts = component.address.split('_')
            if parts[0] not in coms:
                self.client.send_multipart(self.address, b"", b"CLOSE")
                coms.append(parts[0])

    def read_component(self, component_id):
        msg = ""
        try:
            while True:
                _, _, rmsg = self.client.recv_multipart(flags=zmq.NOBLOCK)
                msg += rmsg.decode('utf-8')
        except zmq.ZMQError:
            pass
        if len(msg) > 0:
            msgs = msg[:-1].split('\n')
        else:
            msgs = []
        for msg in msgs:
            comps = msg.split(' ')
            cid = comps[1] + '_' + comps[2]
            if cid in self.input_ids:
                if comps[0] == 'DIn':
                    self.values[self.input_ids[cid]] = not self.values[self.input_ids[cid]]
                elif comps[0] == 'AIn':
                    self.values[self.input_ids[cid]] = int(comps[3])
                elif comps[0] == 'GPIOIn':
                    self.values[self.input_ids[cid]] = not self.values[self.input_ids[cid]]
        return self.values[component_id]

    def write_component(self, component_id, msg):
        # If the intended value for the component differs from the current value, change it
        if not msg == self.values[component_id]:
            parts = self.components[component_id].address.split('_')
            if 'A' in self.components[component_id].address:
                self.client.send_multipart(self.address, b"", 'GPIOOut {} {}\n'.format(parts[0], parts[1]).encode('utf-8'))
            elif 'O' in self.components[component_id].address:
                scaled = msg
                if scaled < 0:
                    scaled = 0
                elif scaled > 2.5:
                    scaled = 2.5
                scaled = round(scaled * 65535 / 2.5)
                self.client.send_multipart(self.address, b"", 'AOut {} {} {}\n'.format(parts[0], parts[1], scaled).encode('utf-8'))
            else:
                self.client.send_multipart(self.address, b"", 'DOut {} {}\n'.format(parts[0], parts[1]).encode('utf-8'))
        self.values[component_id] = msg

    def close_component(self, component_id: str) -> None:
        if 'A' in self.components[component_id].address:
            parts = self.components[component_id].address.split('_')
            self.client.send_multipart(self.address, b"", 'RegGPIO {} {} {}\n'.format(parts[0], parts[1], 0).encode('utf-8'))

    def is_available(self):
        return self.available
