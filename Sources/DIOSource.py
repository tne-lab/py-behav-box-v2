import nidaqmx
from nidaqmx import system
from nidaqmx.constants import (LineGrouping)

from Sources.Source import Source


class DIOSource(Source):

    def __init__(self, dev):
        self.dev = dev
        dev_obj = system.Device(dev)
        dev_obj.reset_device()
        self.components = {}

    def register_component(self, component):
        task = nidaqmx.Task()
        task.do_channels.add_do_chan(component.address, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        task.start()
        self.components[component.id] = component.address

    def close_source(self):
        for c in self.components:
            c.close()

    def read_component(self, component_id):
        # Do I need a stop here as well?
        self.components[component_id].read()

    def write_component(self, component_id, msg):
        self.components[component_id].write(msg)
        # What do enable and send pulse do?
