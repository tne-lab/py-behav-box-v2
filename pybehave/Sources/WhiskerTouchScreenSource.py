from typing import Dict

try:
    import win32gui
except ModuleNotFoundError:
    from pybehave.Utilities.Exceptions import MissingExtraError
    raise MissingExtraError('whisker')

import socket
import subprocess
import threading
import traceback
import time

from pybehave.Components.Component import Component
from pybehave.Sources.Source import Source

IsWhiskerRunning = False


def look_for_program(hwnd, program_name):
    global IsWhiskerRunning
    if program_name in win32gui.GetWindowText(hwnd):
        win32gui.CloseWindow(hwnd)  # Minimize Window
        IsWhiskerRunning = True


class WhiskerTouchScreenSource(Source):

    def __init__(self, address='localhost', port=3233, display_num=0, whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"):
        super().__init__()
        self.available = True
        self.address = address
        self.port = int(port)
        self.display_num = display_num
        self.whisker_path = whisker_path
        self.client = None
        self.running = None
        self.vals = {}

    def initialize(self):
        try:
            win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if not IsWhiskerRunning:
                ws = self.whisker_path
                window = subprocess.Popen(ws)
                time.sleep(2)
                print("WHISKER server started", window)
                win32gui.EnumWindows(look_for_program, 'WhiskerServer')
            if IsWhiskerRunning:
                self.available = True
                self.display_num = self.display_num
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.client.connect((self.address, int(self.port)))
                self.running = threading.Event()
                rt = threading.Thread(target=lambda: self.read())
                rt.start()
                self.client.send('DisplayClaim {}\n'.format(self.display_num).encode('utf-8'))
                self.client.send(b'DisplayEventCoords on\n')
                self.client.send('DisplayCreateDocument {}\n'.format(self.display_num).encode('utf-8'))
                self.client.send('DisplayShowDocument {} {}\n'.format(self.display_num, self.display_num).encode('utf-8'))
                self.client.send('DisplayGetSize {}\n'.format(self.display_num).encode('utf-8'))
        except:
            traceback.print_exc()
            self.available = False


    def close_source(self) -> None:
        self.running.set()

    def read(self):
        while not self.running.is_set():
            msg = self.client.recv(4096).decode()
            print(msg)
            msgs = msg[:-1].split('\n')
            for msg in msgs:
                if msg.startswith('Event:'):
                    split_msg = msg.split(' ')
                    self.vals[split_msg[1]] = (not self.vals[split_msg[1]][0], [int(split_msg[2]), int(split_msg[3])])
                    self.update_component(split_msg[1], self.vals[split_msg[1]])
                elif msg.startswith('Info:'):
                    if 'size: ' in msg:
                        split = msg.split(': ')[2].split(' ')
                        width = int(split[0][2:])
                        height = int(split[1][2:])
                        self.client.send(
                            'DisplayAddObject {} {} rectangle 0 {} {} 0 -pencolour 0 0 0 -brushsolid 0 0 0;DisplaySetObjectEventTransparency {} {} on;DisplaySendToBack {} {}\n'.format(
                                self.display_num, 'background', height - 1, width - 1, self.display_num,
                                'background', self.display_num,
                                'background').encode('utf-8'))
        self.client.send(b'DisplayRelinquishAll\n')
        self.client.close()

    def register_component(self, component, metadata):
        self.components[component.id] = component
        if component.get_type() == Component.Type.DIGITAL_OUTPUT:
            self.client.send(
                'DisplayAddObject {} {} {};DisplaySendToBack {} {}\n'.format(
                    self.display_num, component.id, component.definition, self.display_num, component.id).encode('utf-8'))
        elif component.get_type() == Component.Type.DIGITAL_INPUT:
            self.client.send(
                'DisplaySetEvent {} {} TouchDown {};DisplaySetEvent {} {} TouchUp {}\n'.format(
                    self.display_num, component.obj, component.id,
                    self.display_num, component.obj, component.id
                ).encode('utf-8'))
            self.vals[component.id] = (False, None)

    def write_component(self, component_id, msg):
        if msg:
            self.client.send('DisplayBringToFront {} {}\n'.format(self.display_num, component_id).encode('utf-8'))
        else:
            self.client.send('DisplaySendToBack {} {}\n'.format(self.display_num, component_id).encode('utf-8'))

    def close_component(self, component_id: str) -> None:
        if self.components[component_id].get_type() == Component.Type.DIGITAL_OUTPUT:
            self.client.send('DisplayDeleteObject {} {}\n'.format(self.display_num, component_id).encode('utf-8'))

    def is_available(self):
        return self.available

    @staticmethod
    def metadata_defaults(comp_type: Component.Type = None) -> Dict:
        if comp_type == Component.Type.DIGITAL_OUTPUT:
            return {"definition": ""}
        elif comp_type == Component.Type.DIGITAL_INPUT:
            return {"obj": ""}
        else:
            return {}
