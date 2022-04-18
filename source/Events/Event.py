class Event:
    """
        Simple class defining the base requirements for a Task Event.

        Attributes
        ----------
        entry_time : float
            Time when the event was initiated
        metadata : Object
            Any metadata related to the Event
    """

    def __init__(self, entry_time, metadata=None):
        self.entry_time = entry_time
        self.metadata = metadata
