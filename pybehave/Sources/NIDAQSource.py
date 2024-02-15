import nidaqmx
from nidaqmx import stream_writers
from nidaqmx.constants import (LineGrouping)
import numpy as np
from nidaqmx.system import system

from pybehave.Components.Component import Component
from pybehave.Sources.Source import Source


class NIDAQSource(Source):
    """
        Class defining a Source for interacting with National Instruments DAQs.

        Attributes
        ----------
        dev : Device
            Library representation of DAQ
        components : dict
            Links Component IDs to Component objects
        tasks : dict
            Links Component IDs to DAQ tasks
        streams : dict
            Links Component IDs to DAQ streams

        Methods
        -------
        register_component(_, component)
            Registers the component with the DAQ according to its type
        close_source()
            Closes all tasks
        close_component(component_id)
            Closes the task for a specific Component
        read_component(component_id)
            Requests the current response for the Component from the DAQ
        write_component(component_id, msg)
            Writes a response for the Component to the DAQ
    """

    def __init__(self, dev):
        super(NIDAQSource, self).__init__()
        self.dev = dev
        self.tasks = {}
        self.streams = {}
        self.ao_task = None
        self.ao_stream = None
        self.ao_inds = {}

    def initialize(self):
        dev_obj = system.Device(self.dev)
        dev_obj.reset_device()

    def register_component(self, component, metadata):
        if component.get_type() == Component.Type.DIGITAL_OUTPUT:
            task = nidaqmx.Task()
            task.do_channels.add_do_chan(self.dev + component.address,
                                         line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
            task.start()
            self.tasks[component.id] = task
        elif component.get_type() == Component.Type.ANALOG_OUTPUT:
            if self.ao_task is None:
                self.ao_task = nidaqmx.Task()
            self.ao_task.ao_channels.add_ao_voltage_chan(self.dev + component.address)
            self.ao_stream = stream_writers.AnalogMultiChannelWriter(self.ao_task.out_stream)
            self.ao_inds[component.id] = len(self.ao_inds)

    def close_source(self):
        if self.ao_task is not None:
            self.ao_task.close()
            self.ao_task = None
            self.ao_stream = None
        for task in self.tasks:
            task.close()
        self.tasks = {}

    def close_component(self, component_id):
        if self.components[component_id].get_type() == Component.Type.ANALOG_OUTPUT:
            if self.ao_task is not None:
                self.ao_task.stop()
                self.ao_task.close()
                self.ao_task = None
                self.ao_stream = None
        else:
            self.tasks[component_id].stop()
            self.tasks[component_id].close()

    def write_component(self, component_id, msg):
        if self.components[component_id].get_type() == Component.Type.DIGITAL_OUTPUT:
            self.tasks[component_id].write(msg)
        elif self.components[component_id].get_type() == Component.Type.ANALOG_OUTPUT:
            output = np.zeros((len(self.ao_inds), msg.shape[1]))
            output[self.ao_inds[component_id], :] = np.squeeze(msg)
            if self.ao_task.is_task_done():
                self.ao_task.stop()
            self.ao_task.timing.cfg_samp_clk_timing(self.components[component_id].sr,
                                                    sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                                    samps_per_chan=msg.shape[1])
            self.ao_stream.write_many_sample(output)
            self.ao_task.start()
