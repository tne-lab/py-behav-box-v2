import nidaqmx
from nidaqmx import system, stream_writers
from nidaqmx.constants import (LineGrouping)

from Components.Component import Component
from Sources.Source import Source


class NIDAQSource(Source):

    def __init__(self, dev):
        self.dev = dev
        dev_obj = system.Device(dev)
        dev_obj.reset_device()
        self.tasks = {}
        self.components = {}
        self.streams = {}

    def register_component(self, _, component):
        task = nidaqmx.Task()
        if component.get_type() == Component.Type.DIGITAL_OUTPUT:
            task.do_channels.add_do_chan(self.dev + component.address, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        elif component.get_type() == Component.Type.DIGITAL_INPUT:
            task.di_channels.add_di_chan(self.dev + component.address, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        elif component.get_type() == Component.Type.ANALOG_OUTPUT:
            task.do_channels.add_ao_voltage_chan(self.dev + component.address)
            self.streams[component.id] = stream_writers.AnalogSingleChannelWriter(task.out_stream, auto_start=True)
        elif component.get_type() == Component.Type.ANALOG_INPUT:
            task.di_channels.add_ai_voltage_chan(self.dev + component.address)
            self.streams[component.id] = stream_writers.AnalogSingleChannelReader(task.in_stream, auto_start=True)
        task.start()
        self.tasks[component.id] = task
        self.components[component.id] = component

    def close_source(self):
        for c in self.tasks:
            c.close()

    def close_component(self, component_id):
        self.tasks[component_id].close()
        del self.tasks[component_id]
        del self.components[component_id]

    def read_component(self, component_id):
        # Do I need a stop here as well?
        if self.components[component_id].get_type() == Component.Type.DIGITAL_INPUT:
            return self.tasks[component_id].read()
        elif self.components[component_id].get_type() == Component.Type.ANALOG_INPUT:
            return self.streams[component_id].read_one_sample(0)

    def write_component(self, component_id, msg):
        if self.components[component_id].get_type() == Component.Type.DIGITAL_OUTPUT:
            self.tasks[component_id].write(msg)
        elif self.components[component_id].get_type() == Component.Type.ANALOG_OUTPUT:
            self.tasks[component_id].timing.cfg_samp_clk_timing(int(self.components[component_id].sr), samps_per_chan=msg.shape[1])
            self.streams[component_id].write_many_sample(msg)
