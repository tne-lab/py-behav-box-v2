from Components.Component import Component
import time


class Video(Component):
    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        self.name = None
        super().__init__(source, component_id, component_address, metadata)

    def start(self):
        self.name = str(time.time())
        self.state = True

    def stop(self):
        self.state = False

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.INPUT
