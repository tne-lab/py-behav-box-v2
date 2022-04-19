from source.Components.Component import Component


class StimJim(Component):

    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def trigger(self, ichan, pnum, falling=0):
        self.source.write_component(self.id, "R{},{},{}".format(ichan, pnum, falling))

    def parametrize(self, pnum, o0, o1, per, dur, as0, as1, durs):
        stimulus = "S{},{},{},{},{}".format(stype, pnum, o0, o1, per, dur)
        for i in range(len(as0)):
            stimulus += "; {},{},{}".format(as0[i], as1[i], durs[i])
        self.source.write_component(self.id, stimulus)

    def start(self, pnum, stype="T"):
        self.source.write_component(self.id, "{}{}".format(stype, pnum))

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.OUTPUT
