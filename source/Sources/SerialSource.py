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
        for component in self.components.values():
            self.close_component(component)

    def read_component(self, component_id):
        return self.coms[component_id].readline()

    def write_component(self, component_id, msg):
        if hasattr(self.components[component_id], "terminator"):
            term = self.components[component_id].terminator
        else:
            term = ""
        self.coms[component_id].write(bytes(str(msg) + term, 'utf-8'))

    def is_available(self):
        return True
