import threading
import time

from Components.Toggle import Toggle


class TimedToggle(Toggle):
    """
        Class defining a TimedToggle component in the operant chamber.

        Parameters
        ----------
        source : Source
            The Source related to this Component
        component_id : str
            The ID of this Component
        component_address : str
            The location of this Component for its Source
        metadata : str
            String containing any metadata associated with this Component

        Attributes
        ----------
        state : boolean
            Boolean indicating if the toggle is active
        count : int
            Count of the number of times the toggle has been activated

        Methods
        -------
        toggle(dur)
            Activates the toggle for dur seconds
    """
    def __init__(self, source, component_id, component_address):
        super().__init__(source, component_id, component_address)
        self.count = 0

    def toggle(self, dur):
        if not self.state:
            toggle_thread = threading.Thread(target=lambda: self.toggle_(dur), args=())
            toggle_thread.start()

    def toggle_(self, dur):
        self.source.write_component(self.id, True)
        self.state = True
        self.count += 1
        time.sleep(dur)
        self.source.write_component(self.id, False)
