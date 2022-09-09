from Components.Component import Component


class Toggle(Component):
    """
        Class defining a Toggle component in the operant chamber.

        Parameters
        ----------
        source : Source
            The Source related to this Component
        component_id : str
            The ID of this Component
        component_address : str
            The location of this Component for its Source
        metadata : str
            String containing any metadata associated with this Component

        Attributes
        ----------
        state : boolean
            Boolean indicating if the Component is currently toggled

        Methods
        -------
        get_state()
            Returns state
        toggle(on)
            Sets the Toggle state with the Source
        get_type()
            Returns Component.Type.DIGITAL_OUTPUT
    """

    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def toggle(self, on):
        self.write(on)
        self.state = on

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.DIGITAL_OUTPUT
