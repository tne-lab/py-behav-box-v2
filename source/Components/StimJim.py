from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

from Components.Component import Component

if TYPE_CHECKING:
    from Tasks.Task import Task
    import numpy as np

from Components.Stimmer import Stimmer


class StimJim(Stimmer):

    def __init__(self, task: Task, component_id: str, component_address: str):
        self.state = None
        self.in_buffer = ""
        self.cur_command = None
        self.commands = []
        self.configs = {}
        super().__init__(task, component_id, component_address)

    def trigger(self, ichan: int, pnum: int, falling: int = 0) -> None:
        self.write("R{},{},{}".format(ichan, pnum, falling))

    def parametrize(self, pnum: int, outs: list[int], per: int, dur: int, amps: np.ndarray, durs: list[int]) -> None:
        stimulus = "S{},{},{},{},{}".format(pnum, outs[0], outs[1], per, dur)
        for i in range(amps.shape[1]):
            stimulus += "; "
            for j in range(amps.shape[0]):
                stimulus += "{},".format(amps[j, i])
            stimulus += "{}".format(durs[i])
        self.write(stimulus)

    def update_parameters(self, per: int, amps: np.ndarray, durs: list[int]):
        stimulus = "F{}".format(per)
        for i in range(amps.shape[1]):
            stimulus += "; "
            for j in range(amps.shape[0]):
                stimulus += "{},".format(amps[j, i])
            stimulus += "{}".format(durs[i])
        self.write(stimulus)

    def start(self, pnum: int, stype: str = "T") -> None:
        self.write("{}{}".format(stype, pnum))

    def update(self, value: Union[bytes, str, int]) -> bool:
        print(value)
        if value is not None:
            if isinstance(value, int):
                self.state = value
            else:
                if isinstance(value, str):
                    dec_val = value
                else:
                    dec_val = value.decode('utf-8')
                segs = dec_val.split('\n')
                segs[0] = self.in_buffer + segs[0]
                if not dec_val.endswith('\n'):
                    self.in_buffer = segs[-1]
                    del segs[-1]
                self.commands = []
                for line in segs:
                    if 'Parameters' in line:
                        if self.cur_command is not None:
                            self.commands.append(self.cur_command)
                        self.cur_command = {"command": "P", "id": int(line.split("[")[1].split("]")[0])}
                    elif self.cur_command is not None and self.cur_command["command"] == "P":
                        l_segs = re.split(" +", line)
                        if "mode" in line:
                            if "mode" in self.cur_command:
                                self.cur_command["mode"].append(int(l_segs[2]))
                            else:
                                self.cur_command["mode"] = [int(l_segs[2])]
                        elif "period:" in line:
                            self.cur_command["period"] = int(l_segs[2])
                        elif "duration:" in line:
                            self.cur_command["duration"] = int(l_segs[2])
                        elif len(l_segs) > 1 and l_segs[1].isnumeric():
                            if "stages" in self.cur_command:
                                self.cur_command["stages"].append([l_segs[2], l_segs[4], l_segs[5][:-1]])
                            else:
                                self.cur_command["stages"] = [[l_segs[2], l_segs[4], l_segs[5][:-1]]]
                        elif line[0] == '-':
                            self.commands.append(self.cur_command)
                            self.configs[self.cur_command["id"]] = self.cur_command
                            self.cur_command = None
                    elif 'Started' in line:
                        self.state = int(line[line.rindex(' ')+1:-1])
                        if self.cur_command is not None:
                            self.commands.append(self.cur_command)
                        self.cur_command = None
                    elif 'complete' in line:
                        if self.cur_command is not None:
                            self.commands.append(self.cur_command)
                        self.cur_command = {"command": "C", "id": self.state}
                        self.state = None
                        l_segs = line.split(" ")
                        self.cur_command["n_pulse"] = int(l_segs[3])
                    elif self.cur_command is not None and self.cur_command["command"] == "C" and "Stage" in line:
                        l_segs = re.split(" +", line)
                        if "stages" in self.cur_command:
                            self.cur_command["stages"].append([l_segs[2][:-1], l_segs[3][:-1]])
                        else:
                            self.cur_command["stages"] = [[l_segs[2][:-1], l_segs[3][:-1]]]
                        if len(self.cur_command["stages"]) == len(self.configs[self.cur_command["id"]]["stages"]):
                            self.commands.append(self.cur_command)
                            self.cur_command = None
        return len(self.commands) > 0

    @staticmethod
    def get_type() -> Component.Type:
        return Component.Type.BOTH
