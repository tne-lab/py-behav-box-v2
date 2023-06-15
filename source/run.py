import asyncio
import sys

import qasync
from PyQt5.QtWidgets import QApplication

from Utilities.create_task import create_task
from Workstation.Workstation import Workstation
import faulthandler
import psutil
import os

if __name__ == '__main__':

    p = psutil.Process(os.getpid())
    p.nice(psutil.REALTIME_PRIORITY_CLASS)

    faulthandler.enable()
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    if not os.path.exists("{}\\py-behav\\".format(desktop)):
        os.mkdir("{}\\py-behav\\".format(desktop))
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    ws = Workstation()
    task = create_task(ws.start_workstation())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        ws.exit_handler()
