import threading

import serial

from Components.Component import Component
from Sources.Source import Source


class SerialSource(Source):

    def __init__(self):
        super(SerialSource, self).__init__()
        self.close_events = {}
        self.coms = {}
        self.read_threads = {}

    def register_component(self, task, component):
        super().register_component(task, component)
        com_opened = False
        if component.address not in self.coms:
            self.coms[component.address] = serial.Serial(port=component.address, baudrate=component.baudrate,
                                                         timeout=0.5,
                                                         write_timeout=0)
            com_opened = True
        ct = component.get_type()
        if (ct == Component.Type.INPUT or ct == Component.Type.DIGITAL_INPUT or ct == Component.Type.ANALOG_INPUT or ct == Component.Type.BOTH)\
                and com_opened:
            self.close_events[component.address] = threading.Event()
            self.read_threads[component.address] = threading.Thread(target=self.read, args=[component.address])
            self.read_threads[component.address].start()

    def close_component(self, component_id):
        address = self.components[component_id].address
        del self.components[component_id]
        close_com = True
        for comp in self.components.values():
            if comp.address == address:
                close_com = False
                break
        if close_com:
            self.close_events[address].set()
            self.read_threads[address].join()
            del self.close_events[address]
            del self.read_threads[address]
            del self.coms[address]

    def close_source(self):
        keys = list(self.components.keys())
        for key in keys:
            self.close_component(key)

    def read(self, com):
        while not self.close_events[com].is_set():
            msg = self.coms[com].read(max(1, self.coms[com].in_waiting))
            print(msg)
            if len(msg) > 0:
                for comp in self.components.values():
                    if comp.address == com:
                        self.update_component(comp.id, msg)

    def write_component(self, component_id, msg):
        if hasattr(self.components[component_id], "terminator"):
            term = self.components[component_id].terminator
        else:
            term = ""
        self.coms[self.components[component_id].address].write(bytes(str(msg) + term, 'utf-8'))

    def is_available(self):
        return True
