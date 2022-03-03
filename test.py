from Events.ConsoleLogger import ConsoleLogger
from Sources.EmptySource import EmptySource
from Workstation import Workstation

ws = Workstation()
sources = {"es": EmptySource()}
ws.add_task(0, "SetShift", sources, "test.csv", None, ConsoleLogger())
while True:
    ws.loop()
