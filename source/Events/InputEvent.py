from Events.Event import Event


class InputEvent(Event):
    """
        Class defining an Event for an input to the Task.

        Attributes
        ----------
        input_event : Enum
            Enumerated variable representing the type of input
    """

    def __init__(self, task, input_event, metadata=None):
        super().__init__(task, metadata)
        self.input_event = input_event
