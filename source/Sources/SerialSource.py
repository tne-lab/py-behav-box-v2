import asyncio
from contextlib import suppress

from aioserial import aioserial

from Components.Component import Component
from Sources.Source import Source
from Utilities.create_task import create_task


class SerialSource(Source):

    def __init__(self):
        super(SerialSource, self).__init__()
        self.connections = {}
        self.com_tasks = {}

    async def register_component(self, task, component):
        await super().register_component(task, component)
        if component.address not in self.connections:
            self.connections[component.address] = aioserial.AioSerial(port=component.address,
                                                                      baudrate=component.baudrate)
            self.com_tasks[component.address] = create_task(self.read(component.address))

    async def read(self, com):
        while True:
            data = await self.connections[com].readline_async()
            for comp in self.components.values():
                if comp.address == com and (comp.get_type() == Component.Type.DIGITAL_INPUT or
                                            comp.get_type() == Component.Type.INPUT or
                                            comp.get_type() == Component.Type.ANALOG_INPUT or
                                            comp.get_type() == Component.Type.BOTH):
                    self.update_component(comp.id, data)

    def close_component(self, component_id):
        address = self.components[component_id].address
        del self.components[component_id]
        close_com = True
        for comp in self.components.values():
            if comp.address == address:
                close_com = False
                break
        if close_com:
            self.com_tasks[address].cancel()
            create_task(self.close_com(address))

    async def close_com(self, address):
        with suppress(asyncio.CancelledError):
            await self.com_tasks[address]
        del self.com_tasks[address]
        self.connections[address].close()
        del self.connections[address]

    def close_source(self):
        keys = list(self.components.keys())
        for key in keys:
            self.close_component(key)

    def write_component(self, component_id, msg):
        if hasattr(self.components[component_id], "terminator"):
            term = self.components[component_id].terminator
        else:
            term = ""
        self.connections[self.components[component_id].address].write(bytes(str(msg) + term, 'utf-8'))

    def is_available(self):
        return True
