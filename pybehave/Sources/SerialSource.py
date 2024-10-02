from serial.serialutil import SerialException

try:
    import serial
except ModuleNotFoundError:
    from pybehave.Utilities.Exceptions import MissingExtraError
    raise MissingExtraError('serial')

import threading
from typing import Dict

from pybehave.Components.Component import Component
from pybehave.Sources.Source import Source
import pybehave.Utilities.Exceptions as pyberror


class SerialSource(Source):

    def __init__(self):
        super(SerialSource, self).__init__()
        self.connections = {}
        self.com_tasks = {}
        self.closing = {}

    def register_component(self, component, metadata):
        if component.address not in self.connections:
            try:
                self.connections[component.address] = serial.Serial(port=component.address, baudrate=component.baudrate, timeout=1)
                self.closing[component.address] = False
                self.com_tasks[component.address] = threading.Thread(target=self.read, args=[component.address])
                self.com_tasks[component.address].start()
            except (SerialException, ValueError):
                raise pyberror.ComponentRegisterError(self.component_chambers[component.id])

    def read(self, com):
        while not self.closing[com]:
            data = self.connections[com].read_until(expected='\n', size=None)
            if len(data) > 0:
                for comp in self.components.values():
                    if comp.address == com and (comp.get_type() == Component.Type.DIGITAL_INPUT or
                                                comp.get_type() == Component.Type.INPUT or
                                                comp.get_type() == Component.Type.ANALOG_INPUT or
                                                comp.get_type() == Component.Type.BOTH):
                        self.update_component(comp.id, data)
        del self.com_tasks[com]
        del self.closing[com]
        self.connections[com].close()
        del self.connections[com]

    def close_component(self, component_id):
        address = self.components[component_id].address
        del self.components[component_id]
        close_com = True
        for comp in self.components.values():
            if comp.address == address:
                close_com = False
                break
        if close_com:
            self.closing[address] = True

    def close_source(self):
        keys = list(self.components.keys())
        for key in keys:
            self.close_component(key)

    def write_component(self, component_id, msg):
        if hasattr(self.components[component_id], "terminator"):
            term = self.components[component_id].terminator
        else:
            term = ""
        self.connections[self.components[component_id].address].write(bytes(str(msg) + term, 'utf-8'))

    @staticmethod
    def metadata_defaults(comp_type: Component.Type = None) -> Dict:
        return {"baudrate": 9600, "terminator": ""}
