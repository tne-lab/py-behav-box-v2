from source.Events.Event import Event


class FinalStateEvent(Event):
    """
        Class defining an Event for a Task's final state.

        Attributes
        ----------
        final_state : Enum
            Enumerated variable representing the final state
    """
    def __init__(self, final_state, entry_time, metadata=None):
        super().__init__(entry_time, metadata)
        self.final_state = final_state
