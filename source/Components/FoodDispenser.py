import threading
import time

from source.Components.Component import Component


class FoodDispenser(Component):
    """
        Class defining a FoodDispenser component in the operant chamber.

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
            Boolean indicating if the dispenser is actively dispensing pellets
        pellets : int
            Count of the number of pellets that have been dispensed

        Methods
        -------
        dispense()
            Dispenses a single pellet
        get_state()
            Returns state
        get_type()
            Returns Component.Type.OUTPUT
    """
    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)
        self.pellets = 0

    def dispense(self):
        food_thread = threading.Thread(target=lambda: self.give_food(), args=())
        food_thread.start()

    def give_food(self):
        self.source.write_component(self.id, True)
        self.state = True
        self.pellets += 1
        time.sleep(0.7)
        self.source.write_component(self.id, False)

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.OUTPUT
