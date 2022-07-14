import win32gui
import subprocess
import time

from Sources.NIDAQSource import NIDAQSource

IsWhiskerRunning = False


def look_for_program(hwnd, program_name):
    global IsWhiskerRunning
    if program_name in win32gui.GetWindowText(hwnd):
        win32gui.CloseWindow(hwnd)  # Minimize Window
        IsWhiskerRunning = True


class NIWhiskerSource(NIDAQSource):

    def __init__(self, dev, whisker_path=r"C:\Program Files (x86)\WhiskerControl\WhiskerServer.exe"):
        super(NIWhiskerSource, self).__init__(dev)
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
