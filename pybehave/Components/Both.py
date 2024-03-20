from __future__ import annotations

from pybehave.Components.Component import Component


class Both(Component):

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.BOTH
