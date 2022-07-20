import serial

from Sources.Source import Source


class OSControllerSource(Source):

    def __init__(self, com):
        self.com = serial.Serial(port=com, baudrate=115200, timeout=0, write_timeout=0)
        self.components = {}
        self.values = {}
        self.buffer = ""

    def register_component(self, _, component):
        self.components[component.id] = component

    def close_source(self):
        self.com.__exit__()

    def read_component(self, component_id):
        # Read from Serial until no characters are remaining
        while self.com.in_waiting > 0:
            character = str(self.com.read())
            # If the command is complete
            if character == "\n":
                # Update the stored value
                self.values[int(self.buffer[1:])] = not self.values[int(self.buffer[1:])]
                self.buffer = ""
            else:  # Otherwise, add to the buffer
                self.buffer += character
        return self.values[component_id]

    def write_component(self, component_id, msg):
        # If the intended value for the component differs from the current value, change it
        if not msg == self.values[component_id]:
            self.values[component_id] = msg
            self.coms[component_id].write(bytes("O"+str(msg)+"\n", 'utf-8'))
