from Components.Component import Component


class SerialTTL(Component):  # Not implemented
    def __init__(self, source, component_id, component_address, metadata=""):
        super().__init__(source, component_id, component_address, metadata)
        self.nchan = metadata.nchan
        self.counts = [0] * self.nchan

    def set(self, chan=0):
        self.counts[chan] += 1
        self.source.write_component(self.id, "s"+str(chan))

    def set_many(self, chans):
        for i in chans:
            self.counts[i] += 1
        self.source.write_component(self.id, "".join("s" + str(e) for e in chans))

    def pulse(self, chan=0):
        self.counts[chan] += 1
        self.source.write_component(self.id, "p"+str(chan))

    def pulse_many(self, chans):
        for i in chans:
            self.counts[i] += 1
        self.source.write_component(self.id, "".join("p" + str(e) for e in chans))

    def set_pulse_many(self, schans, pchans):
        for i in schans:
            self.counts[i] += 1
        for i in pchans:
            self.counts[i] += 1
        self.source.write_component(self.id, "".join("s" + str(e) for e in schans).join("p" + str(e) for e in pchans))

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.DIGITAL_OUTPUT
