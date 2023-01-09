import collections
import pickle
import runpy
from multiprocessing import Process, Pipe
from typing import OrderedDict
import os.path

from Sources.Source import Source
from Components.Component import Component
import numpy as np
import math
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF


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


class BayesBuilder:
    def __init__(self, path, constant, length_scale, length_scale_bounds, noise, restarts, param_ranges):
        self.path = path
        self.constant = constant
        self.length_scale = length_scale
        self.length_scale_bounds = length_scale_bounds
        self.noise = noise
        self.restarts = restarts
        self.param_ranges = param_ranges


class BayesContainer:
    def __init__(self, bb):
        self.path = bb.path
        self.constant = bb.constant
        self.length_scale = bb.length_scale
        self.length_scale_bounds = bb.length_scale_bounds
        self.noise = bb.noise
        self.outcome = np.empty((1, 1))
        self.params = np.empty(1, len(bb.param_ranges))
        self.restarts = bb.restarts
        self.param_ranges = bb.param_ranges
        self.test_params = np.array(np.meshgrid(*bb.param_ranges.values())).T.reshape(-1, len(bb.param_ranges))
        self.gaussian_process = None

    def fit(self, refit_hyper=False):
        if refit_hyper:
            kernel = self.constant * RBF(length_scale=self.length_scale, length_scale_bounds=self.length_scale_bounds)
            self.gaussian_process = GaussianProcessRegressor(kernel=kernel, alpha=self.noise ** 2,
                                                             n_restarts_optimizer=self.restarts)
        else:
            kernel = self.gaussian_process.kernel_.k1.constant_value * RBF(
                length_scale=self.gaussian_process.kernel_.k2.length_scale, length_scale_bounds='fixed')
            self.gaussian_process = GaussianProcessRegressor(kernel=kernel, alpha=self.noise ** 2, n_restarts_optimizer=0)
        self.gaussian_process.fit(self.params, self.outcome)

    def suggest(self):
        mean_prediction, std_prediction = self.gaussian_process.predict(self.test_params, return_std=True)
        soft_max = np.cumsum(np.power(math.e, mean_prediction - std_prediction) / np.sum(
            np.power(math.e, mean_prediction - std_prediction)))
        keys = list(self.param_ranges.keys())
        new_params = self.test_params[np.argmin(np.abs(soft_max - np.random.rand()))]
        return collections.OrderedDict([(keys[i], new_params[i]) for i in range(len(new_params))])

    def add_data(self, outcome, params: OrderedDict):
        np.append(self.outcome, outcome).reshape(-1, 1)
        np.append(self.params, list(params.values())).reshape(-1, len(self.param_ranges))

    def save(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path):
        if os.path.isfile(path):
            file_globals = runpy.run_path(path, {"BayesBuilder": BayesBuilder, "np": np})
            if os.path.isfile(file_globals['bb'].path):
                with open(file_globals['bb'].path, 'rb') as f:
                    return pickle.load(f)
            else:
                return BayesContainer(file_globals['bb'])
        else:
            raise FileNotFoundError


class BayesProcess(Process):

    def __init__(self, inq, outq):
        super(BayesProcess, self).__init__()
        self.inq = inq
        self.outq = outq
        self.bayes = None

    def run(self):
        closing = False
        while not closing:
            command = self.inq.get()
            if command['command'] == 'Register':
                self.bayes = BayesContainer.load(command['file'])
            elif command['command'] == 'NewData':
                self.bayes.add_data(command['outcome'], command['params'])
            elif command['command'] == 'NewDataFit':
                self.bayes.add_data(command['outcome'], command['params'])
                self.bayes.fit()
                self.outq.put(self.bayes.suggest())
            elif command['command'] == 'Suggest':
                self.outq.put(self.bayes.suggest())
            elif command['command'] == 'OptimizeHyper':
                self.bayes.fit(refit_hyper=True)
            elif command['command'] == 'Save':
                self.bayes.save()
            elif command['command'] == 'Close':
                closing = True


class BayesOptSource(Source):

    def __init__(self):
        super(BayesOptSource, self).__init__()
        self.inq = PipeQueue()
        self.outq = PipeQueue()
        self.bayesprocess = BayesProcess(self.outq, self.inq)
        self.components = {}
        self.next_params = {}
        self.available = True

    def register_component(self, _, component: Component) -> None:
        self.components[component.id] = component
        self.outq.put({'command': 'Register', 'id': component.id, 'file': component.address})

    def write_component(self, component_id: str, msg: OrderedDict) -> None:
        self.outq.put(msg)

    def read_component(self, component_id: str) -> OrderedDict:
        if self.inq.poll():
            self.next_params[component_id] = self.inq.get()
        return self.next_params[component_id]

    def close_source(self) -> None:
        self.outq.put({'command': 'Close'})

    def is_available(self):
        return self.available
