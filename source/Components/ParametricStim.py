from Components.Component import Component


class ParametricStim(Component):

    def __init__(self, source, component_id, component_address, metadata=""):
        self.state = False
        super().__init__(source, component_id, component_address, metadata)

    def trigger(self, ichan, pnum, falling=0):
        self.source.write_component(self.id, "R{},{},{}".format(ichan, pnum, falling))

    def parametrize(self,pnum, outs, per, dur, amps, durs):
        stimulus = "S{},{},{},{},{}".format(pnum, outs[0], outs[1], per, dur)
        for i in range(amps.shape[1]):
            stimulus += "; "
            for j in range(amps.shape[0]):
                stimulus += "{},".format(amps[j, i])
            stimulus += "{}".format(durs[i])
        self.source.write_component(self.id, stimulus)

    def start(self, pnum, stype="T"):
        self.source.write_component(self.id, "{}{}".format(stype, pnum))

    def get_state(self):
        return self.state

    def get_type(self):
        return Component.Type.OUTPUT
