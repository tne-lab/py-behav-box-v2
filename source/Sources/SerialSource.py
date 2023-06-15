import asyncio

import serial_asyncio

from Components.Component import Component
from Sources.Source import Source
from Utilities.create_task import create_task


class SerialSource(Source):

    def __init__(self):
        super(SerialSource, self).__init__()
        self.readers = {}
        self.writers = {}
        self.read_tasks = {}

    async def register_component(self, task, component):
        await super().register_component(task, component)
        com_opened = False
        if component.address not in self.readers:
            self.readers[component.address], self.writers[component.address] = await serial_asyncio.open_serial_connection(url=component.address, baudrate=component.baudrate)
            com_opened = True
        ct = component.get_type()
        if (ct == Component.Type.INPUT or ct == Component.Type.DIGITAL_INPUT or ct == Component.Type.ANALOG_INPUT or ct == Component.Type.BOTH)\
                and com_opened:
            self.read_tasks[component.address] = create_task(self.read(component.address))

    def close_component(self, component_id):
        address = self.components[component_id].address
        del self.components[component_id]
        close_com = True
        for comp in self.components.values():
            if comp.address == address:
                close_com = False
                break
        if close_com:
            self.read_tasks[address].cancel()
            self.writers[address].close()
            del self.read_tasks[address]
            del self.writers[address]
            del self.readers[address]

    def close_source(self):
        keys = list(self.components.keys())
        for key in keys:
            self.close_component(key)

    async def read(self, com):
        while True:
            msg = await self.readers[com].read()
            print(msg)
            if len(msg) > 0:
                for comp in self.components.values():
                    if comp.address == com:
                        self.update_component(comp.id, msg)

    def write_component(self, component_id, msg):
        if hasattr(self.components[component_id], "terminator"):
            term = self.components[component_id].terminator
        else:
            term = ""
        self.writers[self.components[component_id].address].write(bytes(str(msg) + term, 'utf-8'))

    def is_available(self):
        return True
