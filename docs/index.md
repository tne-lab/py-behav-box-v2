# Home

![](img/full_gui.jpg)

# Overview

Pybehave is an open source software interface and framework for controlling behavioral experiments in neuroscience and psychology
built around a hardware-agnostic and highly object-oriented design philosophy.

Pybehave separates code for task design from specific hardware implementations to streamline development, accessibility, and
data sharing. This approach, combined with a task-specific GUIs, expedites and simplifies the creation and visualization of complex behavioral tasks.
User created [task](tasks.md) definition files can interact with hardware-specific [source]() files both written in Python. Any and all local
configuration can be handled outside of Python using [Address Files]() and [Protocols]() formatted as CSVs.

All pybehave tasks are coordinated via a [Workstation]() GUI.

Pybehave software and documentation are available on [GitHub](https://github.com/tne-lab/py-behav-box-v2).

# Getting started

## Installation

Get the latest version of pybehave by cloning the [code repository](https://github.com/tne-lab/py-behav-box-v2) to your computer with Git. Cloning the repository
simplifies the process of updating in the future.

Pybehave has the following folder structure:

    -py-behav-box-v2
        environment.yml     # Anaconda environment for dependendencies
        py-behav.bat        # Batch script to launch the GUI
        -source
            -Components     # Abstractions of hardware components
            -Elements       # Visual elements in GUI
            -Events         # Classes for handling events
            -GUIs           # GUI configurations for tasks
            -Sources        # Classes for handling hardware connections
            -Tasks          # Task definition files
            -Utilities      # Various helper functions
            -Workstation    # Classes for managing the pybehave interface

## Dependencies

Due to its hardware-agnostic design philosophy, pybehave has numerous dependencies to support many possible implementations.
To simplify dependency management we recommend using [Anaconda](https://www.anaconda.com/).

Once Anaconda is installed, search for and open Anaconda Navigator. Navigate to the Environments tab then press import. 
With 'Local drive' selected, click the corresponding folder icon and select the `environment.yml` file in the root pybehave
directory. Further details on using Anaconda Navigator to import environments can be found [here](https://docs.anaconda.com/anaconda/navigator/tutorials/manage-environments/#importing-an-environment).

If using Windows, you should then be able to launch the GUI by double-clicking the `py-behav.bat` executable in the pybehave
root directory. A shortcut can be made for the file on the desktop to simplify startup.

The source code for pybehave is in principle cross-platform but has not been thoroughly tested.

## Updating pybehave

Pybehave is explicitly designed in a manner where files for local configuration are separate from the root directory. This
ensures that users can easily update to the newest version of the platform without compromising their experimental files. 
To update, simply pull the latest version from the code repository.

## Running a task

Run the file `py-behav.bat` from the root directory or shortcut, and you will see a GUI window like that shown above.

Select *File->Add Task* from the menu bar. Choose your [task](tasks.md) and a chamber number from the dropdowns or load a [Configuration]() file.

Enter a subject ID in the *Subject* text box and choose an [Address File]() or [Protocol]() if necessary to set up the local configuration of the task.

Any [event]() information such as data saving or external communication or pre-task prompts can be configured by right-clicking the chamber widget
and selecting *Edit Configuration*. All data will be saved to the Desktop in the *py-behav/TASK_NAME/Data/SUBJECT/DATE* folder.

Press the green play button to start the task.

The task can be paused or ended prematurely with the orange pause button or red stop button respectively.

# Troubleshooting

If you encounter problems, take a look at the [issues](https://github.com/tne-lab/py-behav-box-v2/issues) section of the GitHub and leave a new one if your problem isn't resolved.