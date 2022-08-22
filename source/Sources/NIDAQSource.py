import nidaqmx
from nidaqmx import system, stream_writers
from nidaqmx.constants import (LineGrouping)
import numpy as np

from Components.Component import Component
from Sources.Source import Source


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
            Requests the current value for the Component from the DAQ
        write_component(component_id, msg)
            Writes a value for the Component to the DAQ
    """

    def __init__(self, dev):
        self.dev = dev
        try:
            dev_obj = system.Device(dev)
            dev_obj.reset_device()
            self.available = True
        except:
            print("Error when loading DAQ")
            self.available = False
        self.tasks = {}
        self.components = {}
        self.streams = {}
        self.ao_task = None
        self.ao_stream = None
        self.ao_inds = {}

    def register_component(self, _, component):
        if self.available:
            if component.get_type() == Component.Type.DIGITAL_OUTPUT:
                task = nidaqmx.Task()
                task.do_channels.add_do_chan(self.dev + component.address, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                task.start()
                self.tasks[component.id] = task
            elif component.get_type() == Component.Type.DIGITAL_INPUT:
                task = nidaqmx.Task()
                task.di_channels.add_di_chan(self.dev + component.address, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                task.start()
                self.tasks[component.id] = task
            elif component.get_type() == Component.Type.ANALOG_OUTPUT:
                if self.ao_task is None:
                    self.ao_task = nidaqmx.Task()
                self.ao_task.ao_channels.add_ao_voltage_chan(self.dev + component.address)
                self.ao_stream = stream_writers.AnalogMultiChannelWriter(self.ao_task.out_stream)
                self.ao_inds[component.id] = len(self.ao_inds)
            # elif component.get_type() == Component.Type.ANALOG_INPUT:
            #     task.ai_channels.add_ai_voltage_chan(self.dev + component.address)
            #     self.streams[component.id] = stream_writers.AnalogSingleChannelReader(task.in_stream)
            self.components[component.id] = component

    def close_source(self):
        for c in self.tasks:
            c.close()

    def close_component(self, component_id):
        if self.available:
            self.tasks[component_id].close()
            del self.tasks[component_id]
            del self.components[component_id]

    def read_component(self, component_id):
        if self.available:
            # Do I need a stop here as well?
            if self.components[component_id].get_type() == Component.Type.DIGITAL_INPUT:
                return self.tasks[component_id].read()
            elif self.components[component_id].get_type() == Component.Type.ANALOG_INPUT:
                return self.streams[component_id].read_one_sample(0)
        else:
            return None

    def write_component(self, component_id, msg):
        if self.available:
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
                self.ao_stream.write_many_sample(np.squeeze(output))
                self.ao_task.start()
