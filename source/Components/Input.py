from __future__ import annotations

from Components.Component import Component


class Input(Component):

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.INPUT
