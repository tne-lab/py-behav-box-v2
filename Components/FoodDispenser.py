import threading
import time

from Components.Component import Component


class FoodDispenser(Component):
    """
        Class defining a FoodDispenser component in the operant chamber.

        Methods
        -------
        dispense()
            Dispenses a single pellet
        get_state()
            Returns a boolean indicating if the dispenser is actively dispensing food
    """
    def __init__(self, source, component_id, component_address):
        self.state = False
        super().__init__(source, component_id, component_address)
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
