from abc import ABCMeta, abstractmethod
from Tasks.Task import Task


class TaskSequence(Task):
    __metaclass__ = ABCMeta

    def __init__(self, *args):
        super().__init__(*args)
        self.cur_task = None
        self.init_name = None
        self.init_protocol = None
        self.sub_start_time = 0

    def initialize(self):
        self.cur_task = self.ws.switch_task(self, self.init_name, self.init_protocol)

    def init_sequence(self, task, protocol):
        self.init_name = task
        self.init_protocol = protocol

    def switch_task(self, task, seq_state, protocol, metadata=None):
        self.cur_task.stop()
        self.log_sequence_events()
        self.change_state(seq_state, metadata)
        self.cur_task = self.ws.switch_task(self, task, protocol)
        self.start_sub()

    def log_sequence_events(self):
        sub_events = self.cur_task.events
        self.cur_task.events = []
        for event in sub_events:
            event.entry_time += self.sub_start_time - self.start_time
        self.events.extend(sub_events)

    def main_loop(self):
        super(TaskSequence, self).main_loop()
        self.cur_task.main_loop()

    def start_sub(self):
        self.sub_start_time = self.cur_time
        self.cur_task.start()

    def start(self):
        super(TaskSequence, self).start()
        self.start_sub()

    @abstractmethod
    def get_variables(self):
        raise NotImplementedError

    @abstractmethod
    def is_complete(self):
        raise NotImplementedError
