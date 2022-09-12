class AddressFile:

    def __init__(self):
        self.addresses = {}

    def add_component(self, component_id, component_type, source_name, component_address, list_index=None, metadata=None):
        if component_id in self.addresses:
            if list_index is not None:
                if list_index < len(self.addresses[component_id]) and self.addresses[component_id][list_index] is not None:
                    raise ComponentAlreadyRegisteredError
                else:
                    self.addresses[component_id] += [None] * (list_index + 1 - len(self.addresses[component_id]))
                    self.addresses[component_id][list_index] = Address(component_type, source_name, component_address, metadata)
            else:
                raise ComponentAlreadyRegisteredError
        else:
            self.addresses[component_id] = [Address(component_type, source_name, component_address, metadata)]


class Address:

    def __init__(self, component_type, source_name, component_address, metadata=None):
        self.component_type = component_type
        self.source_name = source_name
        self.component_address = component_address
        self.metadata = metadata


class ComponentAlreadyRegisteredError:
    pass
