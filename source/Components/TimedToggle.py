from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Sources.Source import Source
from typing import Union

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
    def __init__(self, source: Source, component_id: str, component_address: str):
        super().__init__(source, component_id, component_address)
        self.count = 0
        self.time_task = None

    def toggle(self, dur: Union[float, bool]) -> None:
        self.count += 1
        if isinstance(dur, float):
            if not self.state:
                self.time_task = asyncio.create_task(self.toggle_(dur))
        elif isinstance(dur, bool):
            if not dur:
                if self.time_task is not None:
                    self.time_task.cancel()
                    self.time_task = None
                self.source.write_component(self.id, False)
                self.state = False
            elif not self.state:
                self.source.write_component(self.id, True)
                self.state = True

    async def toggle_(self, dur: float) -> None:
        self.source.write_component(self.id, True)
        self.state = True
        await asyncio.sleep(dur)
        self.source.write_component(self.id, False)
        self.state = False
