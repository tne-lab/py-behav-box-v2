from abc import ABCMeta, abstractmethod
from Tasks.Task import Task


class TaskSequence(Task):
    __metaclass__ = ABCMeta

    def __init__(self, *args):
        super().__init__(*args)
        self.cur_task = None
        self.init_name = None
        self.init_protocol = None

    def initialize(self):
        self.cur_task = self.ws.switch_task(self, self.init_name, self.init_protocol)

    def init_sequence(self, task_name, protocol):
        self.init_name = task_name
        self.init_protocol = protocol

    def switch_task(self, task_name, protocol):
        self.cur_task.stop()
        self.events.extend(self.cur_task.events)
        self.cur_task = self.ws.switch_task(self, task_name, protocol)
        self.cur_task.start()

    def log_sequence_events(self):
        self.events.extend(self.cur_task.events)
        self.cur_task.events = []

    @abstractmethod
    def get_variables(self):
        raise NotImplementedError

    @abstractmethod
    def is_complete(self):
        raise NotImplementedError
