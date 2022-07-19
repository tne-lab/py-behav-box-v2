from Events.Event import Event


class InitialStateEvent(Event):
    """
        Class defining an Event for a Task's initial state.

        Attributes
        ----------
        initial_state : Enum
            Enumerated variable representing the initial state
    """
    def __init__(self, task, initial_state, metadata=None):
        super().__init__(task, metadata)
        self.initial_state = initial_state
