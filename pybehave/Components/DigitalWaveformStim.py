from pybehave.Components.Component import Component
from pybehave.Components.WaveformStim import WaveformStim


class DigitalWaveformStim(WaveformStim):

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.DIGITAL_OUTPUT
