from abc import ABCMeta, abstractmethod
from Tasks.Task import Task
import time


class TaskSequence(Task):
    __metaclass__ = ABCMeta

    def __init__(self, *args):
        super().__init__(*args)
        self.cur_task = None
        self.init_task = None
        self.init_protocol = None
        self.sub_start_time = 0
        self.init_sequence__()

    @staticmethod
    @abstractmethod
    def get_tasks():
        raise NotImplementedError

    @staticmethod
    def get_sequence_components():
        return {}

    def get_components(self):
        components = {}
        for task in self.get_tasks():
            sub_components = task.get_components()
            for name in sub_components:
                if name not in components:
                    components[name] = sub_components[name]
                elif len(components[name]) < len(sub_components[name]):
                    components[name] = sub_components[name]
        components.update(self.get_sequence_components())
        return components

    def initialize(self):
        self.cur_task = self.ws.switch_task(self, self.init_task, self.init_protocol)

    def init_sequence__(self):
        res = self.init_sequence()
        self.init_task = res[0]
        if len(res) > 1:
            self.init_protocol = res[1]

    @abstractmethod
    def init_sequence(self):
        raise NotImplementedError

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

    def main_loop__(self):
        self.cur_time = time.time()
        self.cur_task.main_loop__()
        self.main_loop()
        self.log_sequence_events()

    def start_sub(self):
        self.sub_start_time = self.cur_time
        self.cur_task.start__()

    def start__(self):
        self.initialize()
        super(TaskSequence, self).start__()
        self.start_sub()
        self.log_sequence_events()

    def pause__(self):
        self.cur_task.pause__()
        self.log_sequence_events()
        super(TaskSequence, self).pause__()

    def stop__(self):
        self.cur_task.stop__()
        self.log_sequence_events()
        super(TaskSequence, self).stop__()

    def resume__(self):
        super(TaskSequence, self).resume__()
        self.cur_task.resume__()
        self.log_sequence_events()
