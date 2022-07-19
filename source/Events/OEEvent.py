from Events.Event import Event


class OEEvent(Event):
    def __init__(self, task, event_type, metadata=None):
        super().__init__(task, metadata)
        self.event_type = event_type
