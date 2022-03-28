from Components.Component import Component


class NosePoke(Component):
    """
        Class defining a NosePoke component in the operant chamber.

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
            Boolean indicating if the nosepoke is currently entered

        Methods
        -------
        check()
            Queries the current state of the nosepoke and outputs POKE_ENTERED if the poke was just entered, POKE_EXIT if
            the poke was just exited, or NO_CHANGE if there was no change from the prior state.
        get_state()
            Returns state
        toggle(on)
            Sets the nosepoke state with the Source (if writing is allowed)
        get_type()
            Returns Component.Type.INPUT
    """
    NO_CHANGE = 0
    POKE_ENTERED = 1
    POKE_EXIT = 2

    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def check(self):
        poked = self.source.read_component(self.id)
        if poked == self.state:
            repeat = True
        else:
            repeat = False
        self.state = poked
        if poked and not repeat:
            return self.POKE_ENTERED
        elif not poked and not repeat:
            return self.POKE_EXIT
        else:
            return self.NO_CHANGE

    def get_state(self):
        return self.state

    def toggle(self, on):
        self.source.write_component(self.id, on)

    def get_type(self):
        return Component.Type.INPUT
