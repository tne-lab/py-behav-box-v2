from source.Events.Event import Event


class InitialStateEvent(Event):
    """
        Class defining an Event for a Task's initial state.

        Attributes
        ----------
        initial_state : Enum
            Enumerated variable representing the initial state
    """
    def __init__(self, initial_state, entry_time, metadata=None):
        super().__init__(entry_time, metadata)
        self.initial_state = initial_state
