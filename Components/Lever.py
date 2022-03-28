from Components.Component import Component


class Lever(Component):
    """
        Class defining a Lever component in the operant chamber.

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
            Boolean indicating if the lever is currently pressed

        Methods
        -------
        check()
            Queries the current state of the lever and outputs LEVER_PRESSED if the lever was pressed, LEVER_DEPRESSED if
            the lever was just released, or NO_CHANGE if there was no change from the prior state.
        get_state()
            Returns state
        toggle(on)
            Sets the lever state with the Source (if writing is allowed)
        get_type()
            Returns Component.Type.INPUT
    """
    NO_CHANGE = 0
    LEVER_PRESSED = 1
    LEVER_DEPRESSED = 2

    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def check(self):
        pressed = self.source.read_component(self.id)
        if pressed == self.state:
            repeat = True
        else:
            repeat = False
        self.state = pressed
        if pressed and not repeat:
            return self.LEVER_PRESSED
        elif not pressed and not repeat:
            return self.LEVER_DEPRESSED
        else:
            return self.NO_CHANGE

    def get_state(self):
        return self.state

    def toggle(self, on):
        self.source.write_component(self.id, on)

    def get_type(self):
        return Component.Type.INPUT
