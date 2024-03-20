from __future__ import annotations

from typing import TYPE_CHECKING

from pybehave.Tasks.TimeoutManager import Timeout

if TYPE_CHECKING:
    from pybehave.Tasks.Task import Task
from typing import Union

from pybehave.Components.Toggle import Toggle


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
    def __init__(self, task: Task, component_id: str, component_address: str):
        super().__init__(task, component_id, component_address)
        self.count = 0

    def toggle(self, dur: Union[float, bool]) -> None:
        self.count += 1
        if isinstance(dur, float):
            if not self.state:
                self.write(True)
                self.state = True
                self.task.tp.tm.reset_timeout(Timeout(self.id, self.task.metadata["chamber"], dur, self.toggle_, ()))
        elif isinstance(dur, bool):
            if not dur:
                self.task.tp.tm.cancel_timeout(self.id)
                self.write(False)
                self.state = False
            elif not self.state:
                self.write(True)
                self.state = True

    def toggle_(self) -> None:
        self.write(False)
        self.state = False
