from enum import Enum

from Tasks.Task import Task


class ClosedLoopSequence(Task):
    class States(Enum):
        PRE_RAW = 0
        PRE_ERP = 1
        CLOSED_LOOP = 2
        PMA = 4
        POST_ERP = 4
        POST_RAW = 5

    def __init__(self, *args):
        super().__init__(*args)
        self.init_sequence("Raw", self.pre_raw_protocol)

    def start(self):
        self.state = self.States.PRE_RAW
        super(ClosedLoopSequence, self).start()

    def main_loop(self):
        super().main_loop()
        if self.state == self.States.PRE_RAW and self.cur_task.is_complete():
            self.switch_task("ERP", self.States.PRE_ERP, self.pre_erp_protocol)
        elif self.state == self.States.PRE_ERP and self.cur_task.is_complete():
            self.switch_task("ClosedLoop", self.States.CLOSED_LOOP, self.closed_loop_protocol)
        elif self.state == self.States.CLOSED_LOOP and self.cur_task.is_complete():
            self.switch_task("PMA", self.States.PMA, self.pma_protocol)
        elif self.state == self.States.PMA and self.cur_task.is_complete():
            self.switch_task("ERP", self.States.POST_ERP, self.post_erp_protocol)
        elif self.state == self.States.POST_ERP and self.cur_task.is_complete():
            self.switch_task("Raw", self.States.POST_RAW, self.post_raw_protocol)
        self.log_sequence_events()

    def get_variables(self):
        return {
            'pre_raw_protocol': None,
            'pre_erp_protocol': None,
            'closed_loop_protocol': None,
            'pma_protocol': None,
            'post_erp_protocol': None,
            'post_raw_protocol': None
        }

    def is_complete(self):
        return self.state == self.States.POST_RAW and self.cur_task.is_complete()
