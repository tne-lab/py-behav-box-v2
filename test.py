from Events.ConsoleLogger import ConsoleLogger
from Sources.DIOSource import DIOSource
from Sources.EmptySource import EmptySource
from Sources.WhiskerTouchScreenSource import WhiskerTouchScreenSource
from Workstation import Workstation

ws = Workstation()
sources = {"es": EmptySource(), "wtss": WhiskerTouchScreenSource(), "ds": DIOSource('Dev2')}
ws.add_task(0, "DPAL", sources, "test.csv", None, ConsoleLogger())
while True:
    ws.loop()
