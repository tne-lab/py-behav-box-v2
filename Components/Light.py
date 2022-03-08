from Components.Component import Component


class Light(Component):
    """
        Class defining a Light component in the operant chamber.

        Methods
        -------
        get_state()
            Returns True if the light is currently lit
        toggle(on)
            Sets the light state with the Source
    """

    def __init__(self, source, component_id, component_address):
        self.state = False
        super().__init__(source, component_id, component_address)

    def toggle(self, on):
        self.source.write_component(self.id, on)
        self.state = on

    def get_state(self):
        return self.state
