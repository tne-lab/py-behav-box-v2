import nidaqmx
from nidaqmx import system
from nidaqmx.constants import (LineGrouping)
import win32gui
import subprocess
import time

from Components.Component import Component
from Sources.Source import Source

IsWhiskerRunning = False


def look_for_program(hwnd, program_name):
    global IsWhiskerRunning
    if program_name in win32gui.GetWindowText(hwnd):
        win32gui.CloseWindow(hwnd)  # Minimize Window
        IsWhiskerRunning = True


class NIWhiskerSource(Source):

    def __init__(self, dev, whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"):
        self.dev = dev
        dev_obj = system.Device(dev)
        dev_obj.reset_device()
        self.tasks = {}
        self.components = {}
        self.path = whisker_path
        win32gui.EnumWindows(look_for_program, 'WhiskerServer')
        if not IsWhiskerRunning:
            try:
                ws = r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"
                window = subprocess.Popen(ws)
                time.sleep(2)
                print("WHISKER server started", window)
                win32gui.EnumWindows(self.lookForProgram, None)
            except:
                print("Could not start WHISKER server")

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

    def close_component(self, component_id):
        self.tasks[component_id].close()
        del self.tasks[component_id]
        del self.components[component_id]

    def read_component(self, component_id):
        # Do I need a stop here as well?
        return self.tasks[component_id].read()

    def write_component(self, component_id, msg):
        if not self.components[component_id].get_type() == Component.Type.INPUT:
            self.tasks[component_id].write(msg)
