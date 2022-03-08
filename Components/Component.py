from abc import ABCMeta, abstractmethod
from enum import Enum


class Component:
    __metaclass__ = ABCMeta
    """
        Abstract class defining the base requirements for a feature that receives input from or outputs to a Source

        Methods
        -------
        get_state()
            Returns the current state the component is in (no type restrictions)
    """

    class Type(Enum):
        INPUT = 0
        OUTPUT = 1
        BOTH = 2

    def __init__(self, source, component_id, component_address):
        self.id = component_id  # The unique identifier for the component or set of related components
        self.address = component_address  # The platform-specific address for the component
        self.source = source  # The source that is used to identify the component
        source.register_component(self)

    @abstractmethod
    def get_state(self): raise NotImplementedError

    @abstractmethod
    def get_type(self): raise NotImplementedError

