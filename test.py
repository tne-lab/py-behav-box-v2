from Events.ConsoleLogger import ConsoleLogger
from Sources.EmptySource import EmptySource
from Sources.EmptyTouchScreenSource import EmptyTouchScreenSource
from Workstation import Workstation

ws = Workstation()
sources = {"es": EmptySource(), "etss": EmptyTouchScreenSource((1024, 768))}
ws.add_task(0, "DPAL", sources, "test.csv", None, ConsoleLogger())
while True:
    ws.loop()
