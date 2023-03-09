import traceback

import zmq

from Sources.Source import Source

from Components.Component import Component

from Utilities.Exceptions import ComponentRegisterError


class OSControllerSource(Source):

    def __init__(self, address='127.0.0.1', port=9296):
        super(OSControllerSource, self).__init__()
        try:
            context = zmq.Context.instance()
            self.client = context.socket(zmq.DEALER)
            self.client.setsockopt(zmq.RCVHWM, 0)
            self.client.setsockopt(zmq.SNDHWM, 0)
            self.client.connect("tcp://{}:{}".format(address, port))
            poll = zmq.Poller()
            poll.register(self.client, zmq.POLLIN)
            self.client.send(b"READY")
            sockets = dict(poll.poll(1000))
            if sockets:
                self.client.recv()
                self.available = True
            else:
                self.available = False
        except:
            traceback.print_exc()
            self.available = False
        self.components = {}
        self.input_ids = {}
        self.values = {}
        self.buffer = ""

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
            self.client.send('RegGPIO {} {} {}\n'.format(parts[0], parts[1], tp).encode('utf-8'))
        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.DIGITAL_OUTPUT:
            if component.id not in self.values:
                self.values[component.id] = False
        else:
            self.values[component.id] = 0

        if component.get_type() == Component.Type.DIGITAL_INPUT or component.get_type() == Component.Type.ANALOG_INPUT:
            self.input_ids[component.address] = component.id

    def close_source(self):
        self.client.send(b"CLOSE")
        self.client.close()

    def read_component(self, component_id):
        msg = ""
        try:
            while True:
                rmsg = self.client.recv(flags=zmq.NOBLOCK)
                msg += rmsg.decode()
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
            if isinstance(self.components[component_id].address, list):
                comps = self.components[component_id].address
            else:
                comps = [self.components[component_id].address]
            command = ""
            for comp in comps:
                parts = comp.split('_')
                if 'A' in self.components[component_id].address:
                    command += 'GPIOOut {} {}\n'.format(parts[0], parts[1])
                elif 'O' in self.components[component_id].address:
                    scaled = msg
                    if scaled < 0:
                        scaled = 0
                    elif scaled > 2.5:
                        scaled = 2.5
                    scaled = round(scaled * 65535 / 2.5)
                    command += 'AOut {} {} {}\n'.format(parts[0], parts[1], scaled)
                else:
                    command += 'DOut {} {}\n'.format(parts[0], parts[1])
            self.client.send(command.encode('utf-8'))
        self.values[component_id] = msg

    def close_component(self, component_id: str) -> None:
        if component_id in self.components:
            if 'A' in self.components[component_id].address:
                parts = self.components[component_id].address.split('_')
                self.client.send('RegGPIO {} {} {}\n'.format(parts[0], parts[1], 0).encode('utf-8'))
            del self.components[component_id]

    def is_available(self):
        return self.available
