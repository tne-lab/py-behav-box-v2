from multiprocessing import Process

import nidaqmx
from nidaqmx import system, stream_writers
from nidaqmx.constants import (LineGrouping)
import numpy as np

from Components.Component import Component
from Sources.Source import Source
from Utilities.PipeQueue import PipeQueue


class NIProcess(Process):
    def __init__(self, dev, inq, outq):
        super(NIProcess, self).__init__()
        self.inq = inq
        self.outq = outq
        self.dev = dev
        try:
            dev_obj = system.Device(dev)
            dev_obj.reset_device()
            self.available = True
        except:
            self.available = False
        self.tasks = {}
        self.streams = {}
        self.ao_task = None
        self.ao_stream = None
        self.ao_inds = {}

    def run(self):
        closing = False
        while not closing:
            command = self.inq.get()
            if command['command'] == 'CloseProcess':
                if self.ao_task is not None:
                    self.ao_task.close()
                    self.ao_task = None
                    self.ao_stream = None
                for task in self.tasks:
                    task.close()
                self.tasks = {}
                closing = True
            elif command['command'] == 'CloseComponent':
                if command['type'] == 'AO':
                    if self.ao_task is not None:
                        self.ao_task.close()
                        self.ao_task = None
                        self.ao_stream = None
                else:
                    self.tasks[command['id']].close()
            elif command['command'] == 'Register':
                if command['type'] == 'DO':
                    task = nidaqmx.Task()
                    task.do_channels.add_do_chan(self.dev + command['address'],
                                                 line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    task.start()
                    self.tasks[command['id']] = task
                elif command['type'] == 'DI':
                    task = nidaqmx.Task()
                    task.di_channels.add_di_chan(self.dev + command['address'],
                                                 line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
                    task.start()
                    self.tasks[command['id']] = task
                elif command['type'] == 'AO':
                    if self.ao_task is None:
                        self.ao_task = nidaqmx.Task()
                    self.ao_task.ao_channels.add_ao_voltage_chan(self.dev + command['address'])
                    self.ao_stream = stream_writers.AnalogMultiChannelWriter(self.ao_task.out_stream)
                    self.ao_inds[command['id']] = len(self.ao_inds)
            elif command['command'] == 'Read':
                if self.available:
                    if command['type'] == 'DI':
                        self.outq.put({'id': command['id'], 'data': self.tasks[command['id']].read()})
                    elif command['type'] == 'AI':
                        self.outq.put({'id': command['id'], 'data': self.streams[command['id']].read_one_sample(0)})
                else:
                    self.outq.put(None)
            elif command['command'] == 'Write':
                if self.available:
                    if command['type'] == 'DO':
                        self.tasks[command['id']].write(command['msg'])
                    elif command['type'] == 'AO':
                        output = np.zeros((len(self.ao_inds), command['msg'].shape[1]))
                        output[self.ao_inds[command['id']], :] = np.squeeze(command['msg'])
                        if self.ao_task.is_task_done():
                            self.ao_task.stop()
                        self.ao_task.timing.cfg_samp_clk_timing(command['sr'],
                                                                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                                                samps_per_chan=command['msg'].shape[1])
                        self.ao_stream.write_many_sample(output)
                        self.ao_task.start()


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
        self.inq = PipeQueue()
        self.outq = PipeQueue()
        self.niprocess = NIProcess(dev, self.outq, self.inq)
        self.niprocess.start()
        self.values = {}

    def register_component(self, _, component):
        command = {'command': 'Register', 'id': component.id, 'address': component.address}
        if component.get_type() == Component.Type.DIGITAL_OUTPUT:
            command['type'] = 'DO'
        elif component.get_type() == Component.Type.DIGITAL_INPUT:
            command['type'] = 'DI'
            self.values[component.id] = 0
        elif component.get_type() == Component.Type.ANALOG_OUTPUT:
            command['type'] = 'AO'
        self.outq.put(command)
        self.components[component.id] = component

    def close_source(self):
        self.outq.put({'command': 'CloseProcess'})
        self.values = {}

    def close_component(self, component_id):
        command = {'command': 'CloseComponent', 'id': component_id}
        if self.components[component_id].get_type() == Component.Type.DIGITAL_OUTPUT:
            command['type'] = 'DO'
        elif self.components[component_id].get_type() == Component.Type.DIGITAL_INPUT:
            command['type'] = 'DI'
            del self.values[component_id]
        elif self.components[component_id].get_type() == Component.Type.ANALOG_OUTPUT:
            command['type'] = 'AO'
        self.outq.put(command)

    def read_component(self, component_id):
        while self.inq.poll():
            result = self.inq.get()
            self.values[result['id']] = result['data']
        if self.is_available():
            command = {'command': 'Read', 'id': component_id}
            if self.components[component_id].get_type() == Component.Type.DIGITAL_INPUT:
                command['type'] = 'DI'
            elif self.components[component_id].get_type() == Component.Type.ANALOG_INPUT:
                command['type'] = 'AI'
            self.outq.put(command)
            return self.values[component_id]
        else:
            return None

    def write_component(self, component_id, msg):
        if self.is_available():
            command = {'command': 'Write', 'id': component_id, 'msg': msg}
            if self.components[component_id].get_type() == Component.Type.DIGITAL_OUTPUT:
                command['type'] = 'DO'
            elif self.components[component_id].get_type() == Component.Type.ANALOG_OUTPUT:
                command['type'] = 'AO'
                command['sr'] = self.components[component_id].sr
            self.outq.put(command)

    def is_available(self):
        return self.niprocess.available
