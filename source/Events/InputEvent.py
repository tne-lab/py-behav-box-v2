from Events.Event import Event


class InputEvent(Event):
    """
        Class defining an Event for an input to the Task.

        Attributes
        ----------
        input_event : Enum
            Enumerated variable representing the type of input
    """

    def __init__(self, input_event, entry_time, metadata=None):
        super().__init__(entry_time, metadata)
        self.input_event = input_event
