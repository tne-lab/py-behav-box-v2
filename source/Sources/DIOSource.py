import nidaqmx
from nidaqmx import system
from nidaqmx.constants import (LineGrouping)

from source.Components.Component import Component
from Sources.Source import Source


class DIOSource(Source):

    def __init__(self, dev):
        self.dev = dev
        dev_obj = system.Device(dev)
        dev_obj.reset_device()
        self.tasks = {}
        self.components = {}

    def register_component(self, _, component):
        task = nidaqmx.Task()
        if component.get_type() == Component.Type.OUTPUT:
            task.do_channels.add_do_chan(self.dev + component.address, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        elif component.get_type() == Component.Type.INPUT:
            task.di_channels.add_di_chan(self.dev + component.address, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        task.start()
        self.tasks[component.id] = task
        self.components[component.id] = component

    def close_source(self):
        for c in self.tasks:
            c.close()

    def read_component(self, component_id):
        # Do I need a stop here as well?
        return self.tasks[component_id].read()

    def write_component(self, component_id, msg):
        if not self.components[component_id].get_type() == Component.Type.INPUT:
            self.tasks[component_id].write(msg)
        # What do enable and send pulse do?
