import asyncio

import serial_asyncio

from Components.Component import Component
from Sources.Source import Source


class SerialSource(Source):
    class ReaderWriter(asyncio.Protocol):
        def connection_made(self, transport):
            self.transport = transport
            self.com = transport.serial.port

        def connect_to_source(self, source):
            self.source = source

        def data_received(self, data):
            for comp in self.source.components.values():
                if comp.address == self.com and (comp.get_type() == Component.Type.DIGITAL_INPUT or
                                                 comp.get_type() == Component.Type.INPUT or
                                                 comp.get_type() == Component.Type.ANALOG_INPUT or
                                                 comp.get_type() == Component.Type.BOTH):
                    self.source.update_component(comp.id, data)

    def __init__(self):
        super(SerialSource, self).__init__()
        self.connections = {}

    async def register_component(self, task, component):
        await super().register_component(task, component)
        if component.address not in self.connections:
            self.connections[component.address] = await serial_asyncio.create_serial_connection(asyncio.get_event_loop(), self.ReaderWriter, component.address, baudrate=component.baudrate)
            self.connections[component.address][1].connect_to_source(self)

    def close_component(self, component_id):
        address = self.components[component_id].address
        del self.components[component_id]
        close_com = True
        for comp in self.components.values():
            if comp.address == address:
                close_com = False
                break
        if close_com:
            self.connections[address][0].close()
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
        self.connections[self.components[component_id].address][0].serial.write(bytes(str(msg) + term, 'utf-8'))

    def is_available(self):
        return True
