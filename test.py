from Events.ConsoleLogger import ConsoleLogger
from Sources.DIOSource import DIOSource
from Sources.EmptySource import EmptySource
from Sources.WhiskerTouchScreenSource import WhiskerTouchScreenSource
from Sources.EmptyTouchScreenSource import EmptyTouchScreenSource
from Sources.VideoSource import VideoSource
from Workstation import Workstation

ws = Workstation()
# sources = {"es": EmptySource(), "wtss": WhiskerTouchScreenSource(), "ds": DIOSource("Dev2"), "vs": VideoSource()}
sources = {"es": EmptySource(), "etss": EmptyTouchScreenSource((1024, 768))}
ws.add_task(0, "DPAL", sources, "test.csv", None, ConsoleLogger())
ws.add_task(1, "SetShift", sources, "test.csv", None, ConsoleLogger())
ws.add_task(2, "FearConditioning", sources, "test.csv", None, ConsoleLogger())
ws.add_task(3, "FiveChoice", sources, "test.csv", None, ConsoleLogger())
ws.start_task(0)
ws.start_task(1)
ws.start_task(2)
ws.start_task(3)
while True:
    ws.loop()
