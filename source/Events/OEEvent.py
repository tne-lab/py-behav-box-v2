from source.Events.Event import Event


class OEEvent(Event):
    def __init__(self, event_type, entry_time, metadata=None):
        super().__init__(entry_time, metadata)
        self.event_type = event_type
