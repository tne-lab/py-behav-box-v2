import serial

from source.Components.Component import Component
from Sources.Source import Source


class SerialSource(Source):

    def __init__(self):
        self.coms = {}
        self.components = {}

    def register_component(self, _, component):
        self.coms[component.id] = serial.Serial(port=component.address, baudrate=component.baudrate, timeout=component.timeout)
        self.components[component.id] = component

    def close_source(self):
        pass

    def read_component(self, component_id):
        return self.coms[component_id].readline()

    def write_component(self, component_id, msg):
        self.coms[component_id].write(bytes(msg, 'utf-8'))
