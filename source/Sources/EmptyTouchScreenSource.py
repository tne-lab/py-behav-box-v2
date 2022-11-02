from Sources.Source import Source
import ast


class EmptyTouchScreenSource(Source):
    """
        Class defining a Source for a TouchScreen without an external connection.

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

    def __init__(self, display_size):
        super(EmptyTouchScreenSource, self).__init__()
        self.display_size = ast.literal_eval(display_size)

    def register_component(self, _, component):
        self.components[component.id] = component.address

    def read_component(self, component_id):
        return []

    def write_component(self, component_id, msg):
        pass

    def is_available(self):
        return True
