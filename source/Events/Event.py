class Event:
    """
        Simple class defining the base requirements for a Task Event.

        Attributes
        ----------
        task : Task
            Task the event corresponds to
        metadata : Object
            Any metadata related to the Event
    """

    def __init__(self, task, metadata=None):
        self.task = task
        self.entry_time = task.cur_time - task.start_time
        self.metadata = metadata
