from source.Events.Event import Event


class StateChangeEvent(Event):
    """
        Class defining an Event for a Task state change.

        Attributes
        ----------
        initial_state : Enum
            Enumerated variable representing the initial state of the Task
        new_state : Enum
            Enumerated variable representing the new state of the Task
    """

    def __init__(self, initial_state, new_state, entry_time, metadata=None):
        super().__init__(entry_time, metadata)
        self.initial_state = initial_state
        self.new_state = new_state
