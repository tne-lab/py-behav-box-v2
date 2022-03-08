from Components.Component import Component


class Toggle(Component):
    """
        Class defining a Toggle component in the operant chamber.

        Methods
        -------
        get_state()
            Returns True if the Component is currently active
        toggle(on)
            Sets the Toggle state with the Source
    """

    def __init__(self, source, component_id, component_address):
        self.state = False
        super().__init__(source, component_id, component_address)

    def toggle(self, on):
        self.source.write_component(self.id, on)
        self.state = on

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.OUTPUT
