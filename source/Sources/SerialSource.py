import threading
from multiprocessing import Process

import serial

from Components.Component import Component
from Sources.Source import Source
from Utilities.PipeQueue import PipeQueue


class SerialProcess(Process):
    def __init__(self, inq, outq):
        super().__init__()
        self.inq = inq
        self.outq = outq
        self.coms = {}
        self.components = {}
        self.threads = {}
        self.close_events = {}

    def run(self):
        closing = False
        while not closing:
            command = self.inq.get()
            if command['command'] == 'CloseProcess':
                closing = True
                for com in self.components.keys():
                    threading.Thread(target=self.close_com, args=[com]).start()
            elif command['command'] == 'CloseComponent':
                threading.Thread(target=self.close_com, args=[command['id']]).start()
            elif command['command'] == 'Register':
                if command['address'] not in self.coms:
                    self.coms[command['address']] = serial.Serial(port=command['address'], baudrate=command['baudrate'],
                                                                  timeout=0.5,
                                                                  write_timeout=0)
                    self.close_events[command['address']] = threading.Event()
                    self.threads[command['address']] = threading.Thread(target=self.read, args=[command['address']])
                    self.threads[command['address']].start()
                self.components[command['id']] = command['address']
            elif command['command'] == 'Write':
                self.coms[self.components[command['id']]].write(bytes(str(command['msg']), 'utf-8'))

    def read(self, com_id):
        while not self.close_events[com_id].is_set():
            msg = self.coms[com_id].read(max(1, self.coms[com_id].in_waiting))
            if len(msg) > 0:
                self.outq.put({'id': com_id, 'msg': msg})

    def close_com(self, comp_id):
        com_id = self.components[comp_id]
        del self.components[comp_id]
        if com_id not in self.components.values():
            self.close_events[com_id].set()
            self.threads[com_id].join()
            self.coms[com_id].__exit__()
            del self.coms[com_id]
            del self.threads[com_id]
            del self.close_events[com_id]


class SerialSource(Source):

    def __init__(self):
        super(SerialSource, self).__init__()
        self.inq = PipeQueue()
        self.outq = PipeQueue()
        self.serialprocess = SerialProcess(self.outq, self.inq)
        self.serialprocess.start()
        self.values = {}

    def register_component(self, _, component):
        self.outq.put(
            {'command': 'Register', 'address': component.address, 'id': component.id, 'baudrate': component.baudrate})
        self.components[component.id] = component
        if component.get_type() == Component.Type.INPUT or component.get_type() == Component.Type.DIGITAL_INPUT \
                or component.get_type() == Component.Type.ANALOG_INPUT or component.get_type() == Component.Type.BOTH:
            self.values[component.id] = ""

    def close_component(self, component_id):
        self.outq.put({'command': 'CloseComponent', 'id': component_id})
        del self.components[component_id]

    def close_source(self):
        self.outq.put({'command': 'CloseProcess'})
        self.components = {}

    def read_component(self, component_id):
        while self.inq.poll():
            result = self.inq.get()
            for component in self.components.values():
                if component.address == result['id']:
                    self.values[component.id] += result['msg'].decode('utf-8')
        msg = self.values[component_id]
        self.values[component_id] = ""
        return msg

    def write_component(self, component_id, msg):
        if hasattr(self.components[component_id], "terminator"):
            term = self.components[component_id].terminator
        else:
            term = ""
        self.outq.put({'command': 'Write', 'id': component_id, 'msg': str(msg) + term})

    def is_available(self):
        return True
