import threading

import serial

from Sources.Source import Source

from Components.Component import Component


class OSControllerSource(Source):

    def __init__(self, com):
        super(OSControllerSource, self).__init__()
        try:
            self.com = serial.Serial(port=com, baudrate=115200, write_timeout=0, dsrdtr=True)
            self.com.dtr = True
            self.com.reset_input_buffer()
            self.com.reset_output_buffer()
            self.available = True
            t = threading.Thread(target=self.read)
            t.start()
        except:
            self.available = False
        self.event = [threading.Event(), threading.Event()]
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
        self.event[0].set()
        self.event[1].wait()
        self.com.__exit__()

    def read(self):
        while not self.event[0].is_set():
            data = self.com.readline().decode('ascii')
            input_id = str(data[1:-1])
            if input_id in self.input_ids:
                self.values[self.input_ids[input_id]] = not self.values[self.input_ids[input_id]]
        self.event[1].set()

    def read_component(self, component_id):
        return self.values[component_id]

    def write_component(self, component_id, msg):
        # If the intended value for the component differs from the current value, change it
        if not msg == self.values[component_id]:
            self.values[component_id] = msg
            self.com.write(("O"+str(self.components[component_id].address)+"\n").encode())

    def is_available(self):
        return self.available
