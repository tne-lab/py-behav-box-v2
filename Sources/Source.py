from abc import ABCMeta, abstractmethod


class Source:
    __metaclass__ = ABCMeta
    """
    Abstract class defining the base requirements for an input/output source. Sources provide data to and receive data
    from components.
    
    Methods
    -------
    register_component(component)
        Registers a component with the Source.
    close_source()
        Safely closes any connections the Source or its components may have
    read_component(component_id)
        Queries the current input to the component described by component_id
    write_component(component_id, msg)
        Sends data msg to the component described by component_id
    """

    @abstractmethod
    def register_component(self, component): raise NotImplementedError

    @abstractmethod
    def close_source(self): raise NotImplementedError

    @abstractmethod
    def read_component(self, component_id): raise NotImplementedError

    @abstractmethod
    def write_component(self, component_id, msg): raise NotImplementedError
