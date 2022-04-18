from source.Components.Component import Component


class Video(Component):
    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.INPUT
