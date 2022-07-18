from enum import Enum

from Tasks.TaskSequence import TaskSequence


class TestSequence(TaskSequence):
    class States(Enum):
        RAW = 0
        PMA = 1

    def __init__(self, *args):
        super().__init__(*args)
        self.init_sequence("Raw", self.raw_protocol)

    def start(self):
        self.state = self.States.RAW
        super(TestSequence, self).start()

    def main_loop(self):
        super().main_loop()
        if self.state == self.States.RAW and self.cur_task.is_complete():
            self.switch_task("PMA", self.States.PMA, self.pma_protocol)
        self.log_sequence_events()

    def get_variables(self):
        return {
            'raw_protocol': None,
            'pma_protocol': None
        }

    def is_complete(self):
        return self.state == self.States.PMA and self.cur_task.is_complete()
