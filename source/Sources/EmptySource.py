from Sources.Source import Source


class EmptySource(Source):
    """
        Class defining a Source without an external connection.

        Attributes
        ----------
        components : dict
            Links Component IDs to Component objects
        values : dict
            Links Component IDs to stored value for each Component

        Methods
        -------
        register_component(component)
            Registers the component
        close_source()
            No functionality
        read_component(component_id)
            Returns the stored value for the component with id component_id
        write_component(component_id, msg)
            Changes the stored value of the component with id component_id to msg
    """

    def __init__(self):
        self.components = {}
        self.values = {}
        self.next_id = 0

    def register_component(self, _, component):
        self.next_id += 1
        self.components[component.id] = component.address
        self.values[component.id] = component.get_state()

    def read_component(self, component_id):
        return self.values[component_id]

    def write_component(self, component_id, msg):
        self.values[component_id] = msg
