from Workstation.Workstation import Workstation
import faulthandler
import os

faulthandler.enable()
desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
if not os.path.exists("{}\\py-behav\\".format(desktop)):
    os.mkdir("{}\\py-behav\\".format(desktop))
ws = Workstation()
