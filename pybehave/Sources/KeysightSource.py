import os
import time

try:
    import keyoscacquire as koa
    from keyoscacquire.fileio import plot_trace
except ModuleNotFoundError:
    from pybehave.Utilities.Exceptions import MissingExtraError
    raise MissingExtraError('keysight')

from pybehave.Sources.Source import Source
from pybehave.Events import PybEvents


class KeysightSource(Source):

    def __init__(self, visa):
        super(KeysightSource, self).__init__()
        self.visa = visa
        self.osc = None
        self.out_paths = {}
        self.shot_num = {}

    def initialize(self):
        self.osc = koa.Oscilloscope(address=self.visa)

    def register_component(self, component, metadata):
        self.out_paths[component.id] = None
        self.shot_num[component.id] = 0

    def close_component(self, component_id):
        del self.components[component_id]
        del self.out_paths[component_id]
        del self.shot_num[component_id]

    def close_source(self):
        for component in self.components:
            self.close_component(component)

    def output_file_changed(self, event: PybEvents.OutputFileChangedEvent) -> None:
        for cid, chamber in self.component_chambers.items():
            if chamber == event.chamber:
                self.out_paths[cid] = event.output_file + "/KeysightShots_" + str(time.time_ns())

    def write_component(self, component_id, msg):
        time, y, channel_numbers = self.osc.get_trace(channels=eval(self.components[component_id].address))
        if not os.path.exists(self.out_paths[component_id]):
            os.makedirs(self.out_paths[component_id])
        plot_trace(time, y, channel_numbers, fname=f"{self.out_paths[component_id]}/{component_id}_{self.shot_num[component_id]}")
        self.shot_num[component_id] += 1

