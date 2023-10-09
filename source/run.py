import multiprocessing

if __name__ == '__main__':
    from Workstation.Workstation import Workstation
    import faulthandler
    import psutil
    import os

    p = psutil.Process(os.getpid())
    p.nice(psutil.REALTIME_PRIORITY_CLASS)

    faulthandler.enable()
    multiprocessing.allow_connection_pickling()
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    if not os.path.exists("{}\\py-behav\\".format(desktop)):
        os.mkdir("{}\\py-behav\\".format(desktop))
    ws = Workstation()
    ws.start_workstation()
