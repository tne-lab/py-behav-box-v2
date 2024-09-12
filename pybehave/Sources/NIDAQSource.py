try:
    import nidaqmx
    from nidaqmx import stream_writers
    from nidaqmx.constants import (LineGrouping)
    import nidaqmx.system as system
except ModuleNotFoundError:
    from pybehave.Utilities.Exceptions import MissingExtraError
    raise MissingExtraError('ni')

from typing import Dict

import numpy as np

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
        self.do_task = None
        self.do_stream = None
        self.ao_inds = {}
        self.do_inds = {}

    def initialize(self):
        dev_obj = system.Device(self.dev)
        dev_obj.reset_device()

    def register_component(self, component, metadata):
        if component.get_type() == Component.Type.DIGITAL_OUTPUT:
            if component.sr is None:
                task = nidaqmx.Task()
                task.do_channels.add_do_chan(self.dev + component.address,
                                             line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                task.start()
                self.tasks[component.id] = task
            else:
                if self.do_task is None:
                    self.do_task = nidaqmx.Task()
                    self.do_task.auto_start = True
                self.do_task.do_channels.add_do_chan(self.dev + component.address)
                self.do_stream = stream_writers.DigitalMultiChannelWriter(self.do_task.out_stream, auto_start=True)
                self.do_inds[component.id] = len(self.do_inds)
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
        if self.do_task is not None:
            self.do_task.close()
            self.do_task = None
            self.do_stream = None
            self.do_inds = {}
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
                del self.ao_inds[component_id]
        else:
            if self.components[component_id].sr is not None:
                if self.do_task is not None:
                    self.do_task.stop()
                    self.do_task.close()
                    self.do_task = None
                    self.do_stream = None
                    del self.do_inds[component_id]
            else:
                self.tasks[component_id].stop()
                self.tasks[component_id].close()

    def write_component(self, component_id, msg):
        if self.components[component_id].get_type() == Component.Type.DIGITAL_OUTPUT:
            if self.components[component_id].sr is not None:
                output = np.zeros((len(self.do_inds), msg.shape[1]))
                output[self.do_inds[component_id], :] = np.squeeze(msg)
                # self.do_task.timing.cfg_samp_clk_timing(self.components[component_id].sr,
                #                                         sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                #                                         samps_per_chan=msg.shape[1])
                self.do_stream.write_many_sample_port_uint32(np.uint32(output))
            else:
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

    @staticmethod
    def metadata_defaults(comp_type: Component.Type = None) -> Dict:
        if comp_type == Component.Type.ANALOG_OUTPUT:
            return {"sr": 30000}
        elif comp_type == Component.Type.DIGITAL_OUTPUT:
            return {"sr": None}
        else:
            return {}
