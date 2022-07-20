import time

import serial

from Sources.Source import Source

from Components.Component import Component


class OSControllerSource(Source):

    def __init__(self, com):
        self.com = serial.Serial(port=com, baudrate=115200, timeout=0, write_timeout=0, dsrdtr=True)
        self.com.dtr = True
        self.com.reset_input_buffer()
        self.com.reset_output_buffer()
        self.components = {}
        self.input_ids = {}
        self.values = {}
        self.buffer = ""

    def register_component(self, _, component):
        self.components[component.id] = component
        if component.get_type() == Component.Type.DIGITAL_INPUT:
            self.input_ids[component.address] = component.id
        self.values[component.id] = False

    def close_source(self):
        self.com.__exit__()

    def read_component(self, component_id):
        # Read from Serial until no characters are remaining
        while self.com.in_waiting > 0:
            character = self.com.read().decode()
            # If the command is complete
            if character == "\n":
                # Update the stored value
                self.values[self.input_ids[str(self.buffer[1:])]] = not self.values[self.input_ids[str(self.buffer[1:])]]
                self.buffer = ""
            else:  # Otherwise, add to the buffer
                self.buffer += character
        return self.values[component_id]

    def write_component(self, component_id, msg):
        # If the intended value for the component differs from the current value, change it
        if not msg == self.values[component_id]:
            self.values[component_id] = msg
            self.com.write(("O"+str(self.components[component_id].address)+"\n").encode())
