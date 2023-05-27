from Workstation.Workstation import Workstation
import faulthandler
import psutil
import os

if __name__ == '__main__':
    p = psutil.Process(os.getpid())
    p.nice(psutil.HIGH_PRIORITY_CLASS)

    faulthandler.enable()
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    if not os.path.exists("{}\\py-behav\\".format(desktop)):
        os.mkdir("{}\\py-behav\\".format(desktop))
    ws = Workstation()
