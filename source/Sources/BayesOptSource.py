import glob
import importlib
import os
import pickle
import queue
import sys
import time
from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np
from matplotlib import pyplot as plt

from Components.Component import Component
from Events import PybEvents
from Sources.ThreadSource import ThreadSource


class BayesObject(ABC):

    def __init__(self):
        self.train_x = None
        self.train_y = None
        self.metadata = None
        self.bounds = None
        self.input_labels = None
        self.output_labels = None
        self.cur_trial = 0

    def initialize(self, train_x: Dict = None, train_y: Dict = None, metadata: Dict = None) -> None:
        self.train_x = train_x
        self.train_y = train_y
        self.metadata = metadata
        self.bounds = metadata["bounds"]
        self.input_labels = metadata["input_labels"]
        self.output_labels = metadata["output_labels"]
        if self.train_x is None:
            self.train_x = {}
            for key in self.input_labels:
                self.train_x[key] = []
        if self.train_y is None:
            self.train_y = {}
            for key in self.output_labels:
                self.train_y[key] = []

    def add_data(self, trials: List[int], train_x: Dict, train_y: Dict) -> None:
        for key in self.input_labels:
            self.train_x[key].append(train_x[key])
        for key in self.output_labels:
            self.train_y[key].append(train_y[key])

    @abstractmethod
    def generate(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def predict(self, x: np.ndarray, output_index: int = 0) -> np.ndarray:
        raise NotImplementedError


class BayesOptSource(ThreadSource):

    def __init__(self):
        super(BayesOptSource, self).__init__()
        self.bayes_objs = {}
        self.plots = {}
        self.output_paths = {}
        self.metadata = {}
        self.data_queue = None
        self.constants = {}

    def initialize(self):
        self.data_queue = queue.Queue()
        while True:
            data = [self.data_queue.get()]
            try:
                data.append(self.data_queue.get_nowait())
            except queue.Empty:
                pass
            tensors = {}
            for datum in data:
                if isinstance(datum, str):
                    if datum not in self.plots:
                        self.plots[datum] = plt.figure()
                        plt.ion()
                        self.plots[datum].show()
                        self.posterior_plot(datum)
                    else:
                        subject_folder = self.output_paths[self.component_chambers[datum]]
                        subject_folder = subject_folder[:subject_folder[:-1].rfind("/")]
                        os.makedirs(os.path.dirname(subject_folder + "/Model/"), exist_ok=True)
                        with open(subject_folder + "/Model/" + datum + "_" + str(time.time_ns()) + ".bayes", "wb") as f:
                            pickle.dump({"x": self.bayes_objs[datum].train_x, "y": self.bayes_objs[datum].train_y}, f)
                else:
                    # Add correct list comprehension
                    if datum["id"] in tensors:
                        tensors[datum["id"]][0].append(datum["trial"])
                        for key in datum["x"]:
                            tensors[datum["id"]][1][key].append(datum["x"][key])
                        for key in datum["y"]:
                            tensors[datum["id"]][1][key].append(datum["y"][key])
                    else:
                        tensors[datum["id"]] = ([datum["trial"]], datum["x"], datum["y"])
            for tensor in tensors:
                self.bayes_objs[tensor].add_data(*tensors[tensor])
                new_params = self.bayes_objs[tensor].generate()
                self.update_component(tensor, new_params)
            for tensor in tensors:
                self.posterior_plot(tensor)

    def register_component(self, component: Component, metadata: Dict) -> None:
        folder = component.address[:component.address.rfind('/')]
        if folder not in sys.path:
            sys.path.insert(1, folder)
        model = component.address.split('/')[-1].split('.py')[0]
        bayes_class = getattr(importlib.import_module(model), model)
        self.bayes_objs[component.id] = bayes_class()
        self.metadata[component.id] = metadata

    def close_source(self) -> None:
        pass

    def close_component(self, component_id: str) -> None:
        pass

    def write_component(self, component_id: str, msg: Dict) -> None:
        if msg["command"] == "initialize":
            # Should there be an option for specifying the data file?
            subject_folder = self.output_paths[self.component_chambers[component_id]]
            subject_folder = subject_folder[:subject_folder[:-1].rfind("/")]
            data_files = glob.glob('**/{}_*.bayes'.format(component_id), root_dir=subject_folder + "/Model", recursive=True)
            print(self.metadata[component_id])
            if len(data_files) == 0:
                self.bayes_objs[component_id].initialize(metadata=self.metadata[component_id])
            else:
                with open(subject_folder + '/Model/' + data_files[-1], 'rb') as f:
                    datafile = pickle.load(f)
                    self.bayes_objs[component_id].initialize(datafile["x"], datafile["y"], metadata=self.metadata[component_id])
            new_params = self.bayes_objs[component_id].generate()
            self.update_component(component_id, new_params)
            self.data_queue.put(component_id)
        elif msg["command"] == "add_data":
            self.data_queue.put({"id": component_id, "trial": msg["x"]["trial"], "x": msg["x"], "y": msg["y"]})
        elif msg["command"] == "save":
            self.data_queue.put(component_id)

    def output_file_changed(self, event: PybEvents.OutputFileChangedEvent) -> None:
        self.output_paths[event.chamber] = event.output_file

    def constants_updated(self, event: PybEvents.ConstantsUpdateEvent) -> None:
        for key in event.constants:
            event.constants[key] = eval(event.constants[key])
        for cid in self.component_chambers:
            if self.component_chambers[cid] == event.chamber:
                self.metadata[cid].update(event.constants)

    def posterior_plot(self, component_id, num_steps=120):  # Show plot in separate thread?
        grid_x, grid_y = np.meshgrid(np.linspace(0, 1, num_steps), np.linspace(0, 1, num_steps), indexing='ij')
        values = np.concatenate([grid_x.reshape(-1, 1), grid_y.reshape(-1, 1)], axis=1)
        post = self.bayes_objs[component_id].predict(values, output_index=0)
        bounds = self.bayes_objs[component_id].bounds
        grid_x = grid_x * (bounds[1][0] - bounds[0][0]) + bounds[0][0]
        grid_y = grid_y * (bounds[1][1] - bounds[0][1]) + bounds[0][1]
        fig = self.plots[component_id]
        fig.clf()
        ax = fig.add_subplot(1, 1, 1)
        CS = ax.contourf(grid_x, grid_y, post.reshape((num_steps, num_steps)), 20)
        y_data = np.asarray(self.bayes_objs[component_id].train_y[self.bayes_objs[component_id].metadata["output"]])
        x_data = []
        if self.bayes_objs[component_id].x_data is not None:
            for key in self.bayes_objs[component_id].input_labels:
                x_data.append(self.bayes_objs[component_id].train_x[key])
            x_data = np.atleast_2d(np.asarray(x_data))
            ax.scatter(x_data[0, :], x_data[1, :], c=y_data, edgecolors='k', norm=CS.norm)
        ax.set_xlabel(self.bayes_objs[component_id].input_labels[0])
        ax.set_ylabel(self.bayes_objs[component_id].input_labels[1])
        fig.subplots_adjust(right=0.9)
        cbar_ax = fig.add_axes([0.93, 0.15, 0.01, 0.7])
        cbar = fig.colorbar(CS, cax=cbar_ax)
        cbar.ax.set_title(self.bayes_objs[component_id].output_labels[0])
        plt.pause(0.005)
