from Components.Component import Component


class TouchScreen(Component):
    def __init__(self, source, component_id, component_address):
        self.image_containers = {}
        self.touches = []
        self.handled_touches = []
        super().__init__(source, component_id, component_address)
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
