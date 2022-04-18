from source.Components.Component import Component


class TouchScreen(Component):
    """
        Class defining a TouchScreen component in the operant chamber.

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
        image_containers : Dictionary
            Links image paths to image data (coordinates and dimensions)
        touches: list
            List of tuples indicating locations on the screen that were recently touched
        handled_touches: list
            List of tuples indicating touches that were parsed by an external process
        display_size: tuple
            Provides the dimensions in pixels of the screen

        Methods
        -------
        add_image(path, coords, dims)
            Adds a new image with the provided path to image_containers linking to coords and dims
        remove_image(path)
            Removes the image at path from image_containers
        refresh()
            Indicates to the Source that the display should be refreshed
        get_touches()
            Query the source for recent touches
        handle()
            Moves all tuples in touches to handled_touches (handle the touches)
        get_state()
            Returns image_containers
        add_touch(coords)
            Adds the location indicated by coords to touches
        get_type()
            Returns Component.Type.BOTH
        """
    def __init__(self, source, component_id, component_address, metadata=""):
        self.image_containers = {}
        self.touches = []
        self.handled_touches = []
        super().__init__(source, component_id, component_address, metadata)
        self.display_size = source.display_size
        self.refresh()

    def add_image(self, path, coords, dim):
        self.image_containers[path] = {"coords": coords, "dim": dim}

    def remove_image(self, path):
        del self.image_containers[path]

    def refresh(self):
        self.source.write_component(self.id, self.image_containers)

    def get_touches(self):
        tl = self.source.read_component(self.id)
        if len(tl) > 0:
            self.touches.append(*tl)

    def handle(self):
        handled = self.touches
        if len(handled) > 0:
            self.handled_touches.append(*handled)
        self.touches = []
        return handled

    def get_state(self):
        return self.image_containers

    def add_touch(self, coords):
        self.touches.append(coords)

    def get_type(self):
        return Component.Type.BOTH
