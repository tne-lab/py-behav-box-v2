from Events.Event import Event


class InitialStateEvent(Event):
    def __init__(self, initial_state, entry_time, metadata=None):
        super().__init__(entry_time, metadata)
        self.initial_state = initial_state
