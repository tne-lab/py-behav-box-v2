from Events.ConsoleLogger import ConsoleLogger
from Sources.DIOSource import DIOSource
from Sources.EmptySource import EmptySource
from Sources.WhiskerTouchScreenSource import WhiskerTouchScreenSource
from Sources.EmptyTouchScreenSource import EmptyTouchScreenSource
from Sources.VideoSource import VideoSource
from Workstation import Workstation

ws = Workstation()
sources = {"es": EmptySource(), "wtss": WhiskerTouchScreenSource(), "ds": DIOSource("Dev2"), "vs": VideoSource()}
ws.add_task(0, "DPAL", sources, "test.csv", None, ConsoleLogger())
while True:
    ws.loop()
