import serial

from Sources.Source import Source


class SerialSource(Source):

    def __init__(self):
        self.coms = {}
        self.components = {}

    def register_component(self, _, component):
        self.coms[component.id] = serial.Serial(port=component.address, baudrate=component.baudrate, timeout=component.timeout, write_timeout=0)
        self.components[component.id] = component

    def close_component(self, component_id):
        self.coms[component_id].__exit__()
        del self.coms[component_id]
        del self.components[component_id]

    def close_source(self):
        for component in self.components:
            self.close_component(component.id)

    def read_component(self, component_id):
        return self.coms[component_id].readline()

    def write_component(self, component_id, msg):
        self.coms[component_id].write(bytes(str(msg), 'utf-8'))
