import asyncio
import os
import traceback

import win32gui

from Components.Component import Component
from Sources.Source import Source
from Utilities.handle_task_result import handle_task_result

IsWhiskerRunning = False


def look_for_program(hwnd, program_name):
    global IsWhiskerRunning
    if program_name in win32gui.GetWindowText(hwnd):
        win32gui.CloseWindow(hwnd)  # Minimize Window
        IsWhiskerRunning = True


class WhiskerLineSource(Source):

    def __init__(self, address='localhost', port=3233,
                 whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"):
        super(WhiskerLineSource, self).__init__()
        self.vals = {}
        self.available = True
        self.address = address
        self.port = int(port)
        self.whisker_path = whisker_path
        self.msg = ""
        self.writer, self.reader, self.read_task = None, None, None

    async def initialize(self):
        try:
            win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if not IsWhiskerRunning:
                ws = self.whisker_path
                os.startfile(ws)
                await asyncio.sleep(2)
                print("WHISKER server started")
                win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if IsWhiskerRunning:
                self.reader, self.writer = await asyncio.open_connection(self.address, self.port)
                self.read_task = asyncio.create_task(self.read())
                self.read_task.add_done_callback(handle_task_result)
            else:
                self.available = False
        except:
            traceback.print_exc()
            self.available = False

    async def read(self):
        while True:
            new_data = await self.reader.readline()
            self.msg += new_data.decode('UTF-8')
            if '\n' in self.msg:
                msgs = self.msg.split('\n')
                self.msg = msgs[-1]
            else:
                msgs = []
            for msg in msgs[:-1]:
                if msg.startswith('Event:'):
                    div = msg.split(' ')[1].rindex("_")
                    cid, direction = msg.split(' ')[1][:div], msg.split(' ')[1][div + 1:]
                    self.update_component(cid, direction == "on")

    async def register_component(self, task, component):
        await super().register_component(task, component)
        if component.get_type() == Component.Type.DIGITAL_INPUT:
            self.writer.write(
                'LineClaim {} -ResetOff;LineSetEvent {} on {};LineSetEvent {} off {}\n'.format(component.address,
                                                                                               component.address,
                                                                                               component.id + "_on",
                                                                                               component.address,
                                                                                               component.id + "_off").encode('utf-8'))
            self.vals[component.id] = False
        else:
            if isinstance(component.address, list):
                addr = component.address
            else:
                addr = [component.address]
            msg = ""
            for a in addr:
                msg += 'LineClaim {} -ResetOff\n'.format(a)
            self.writer.write(msg.encode('utf-8'))

    def close_source(self):
        self.read_task.cancel()
        self.writer.write(b'LineRelinquishAll\n')
        self.writer.close()

    def write_component(self, component_id, msg):
        if isinstance(self.components[component_id].address, list):
            addr = self.components[component_id].address
        else:
            addr = [self.components[component_id].address]
        out = ""
        for a in addr:
            if msg:
                out += 'LineSetState {} on\n'.format(a)
            else:
                out += 'LineSetState {} off\n'.format(a)
        self.writer.write(out.encode('utf-8'))

    def is_available(self):
        return self.available
