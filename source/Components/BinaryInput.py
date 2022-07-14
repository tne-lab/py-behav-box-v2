from Components.Component import Component


class BinaryInput(Component):

    NO_CHANGE = 0
    ENTERED = 1
    EXIT = 2

    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def check(self):
        value = self.source.read_component(self.id)
        if value == self.state:
            repeat = True
        else:
            repeat = False
        self.state = value
        if value and not repeat:
            return self.ENTERED
        elif not value and not repeat:
            return self.EXIT
        else:
            return self.NO_CHANGE

    def get_state(self):
        return self.state

    def toggle(self, on):
        self.source.write_component(self.id, on)

    def get_type(self):
        return Component.Type.DIGITAL_INPUT
