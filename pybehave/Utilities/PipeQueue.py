from multiprocessing import Pipe


class PipeQueue:
    def __init__(self, *args):
        self.out_pipe, self.in_pipe = Pipe(*args)

    def poll(self):
        return self.out_pipe.poll()

    def put(self, item):
        self.in_pipe.send(item)

    def get(self):
        return self.out_pipe.recv()

    def close(self):
        self.out_pipe.close()
        self.in_pipe.close()
