# Home

![](img/full_gui.jpg)

## Overview

Pybehave is an open source software interface and framework for controlling behavioral experiments in neuroscience and psychology
built around a hardware-agnostic and highly object-oriented design philosophy.

Pybehave separates code for task design from specific hardware implementations to streamline development, accessibility, and
data sharing. This approach, combined with a task-specific Graphical User Interfaces (GUIs), expedites and simplifies the creation and visualization of complex behavioral tasks.
User created [task](tasks.md) definition files can interact with hardware-specific [source](sources.md) files both written in Python. Any and all local
configuration can be handled outside of Python using [Address Files](protocols_addressfiles.md#addressfiles) and [Protocols](protocols_addressfiles.md#protocols).

All pybehave tasks are coordinated via a [Workstation](workstation.md) GUI.

Pybehave software and documentation are available on [GitHub](https://github.com/tne-lab/py-behav-box-v2).

## Getting started

### Installation

Get the latest version of pybehave by creating a fork of the [code repository](https://github.com/tne-lab/py-behav-box-v2) to your computer with Git. 
Forking the repository simplifies the process of updating in the future and allows for choosing the selection of available tasks.

Pybehave has the following folder structure:

    -py-behav-box-v2
        environment.yml     # Anaconda environment for dependendencies
        py-behav.bat        # Batch script to launch the GUI
        -source
            -Components     # Abstractions of hardware components
            -Elements       # Visual elements in GUI
            -Events         # Classes for handling events
            -GUIs           # GUI base files for tasks
            -Sources        # Classes for handling hardware connections
            -Tasks          # Task base files
            -Utilities      # Various helper functions
            -Workstation    # Classes for managing the pybehave interface
            -Local          # Git submodule for Task and GUI definitions
                -Tasks
                -GUIs

By default, pybehave uses a [general task repository](https://github.com/tne-lab/all-tasks) for the Translational Neuroengineering Lab. 
If you plan to edit or add tasks, you should make a new repository with the same structure (Tasks and GUIs folders) and 
include any existing tasks you might need. The contents of this repository should be saved in the Local directory.

### Dependencies

Due to its hardware-agnostic design philosophy, pybehave has numerous dependencies to support many possible implementations.
To simplify dependency management we recommend using [Anaconda](https://www.anaconda.com/).

Once Anaconda is installed, search for and open Anaconda Navigator. Navigate to the Environments tab then press import. 
With 'Local drive' selected, click the corresponding folder icon and select the `environment.yml` file in the root pybehave
directory. Further details on using Anaconda Navigator to import environments can be found [here](https://docs.anaconda.com/anaconda/navigator/tutorials/manage-environments/#importing-an-environment).

If using Windows, you should then be able to launch the GUI by double-clicking the `py-behav.bat` executable in the pybehave
root directory. A shortcut can be made for the file on the desktop to simplify startup.

The source code for pybehave is in principle cross-platform but has not been thoroughly tested.

### Updating pybehave

Pybehave is explicitly designed in a manner where files for local configuration are separate from the root directory. This
ensures that users can easily update to the newest version of the platform without compromising their experimental files. 
To update, simply pull the latest version from the upstream base pybehave code repository and the repository referenced by
the *Local* folder.

### Running a task

Run the file `py-behav.bat` from the root directory or shortcut, and you will see a GUI window like that shown above.

Select *File->Add Task* from the menu bar. Choose your [task](tasks.md) and a chamber number from the dropdowns or load a [Configuration](workstation.md#configurations) file.

Enter a subject ID in the *Subject* text box and choose an [Address File](protocols_addressfiles.md#addressfiles) or [Protocol](protocols_addressfiles.md#protocols) if necessary to set up the local configuration of the task.

Any [event](events.md) information such as data saving or external communication or pre-task prompts can be configured by right-clicking the chamber widget
and selecting *Edit Configuration*. All data will be saved to the Desktop in the *py-behav/TASK_NAME/Data/SUBJECT/DATE* folder.

Press the green play button to start the task.

The task can be paused or ended prematurely with the orange pause button or red stop button respectively.

## Troubleshooting

If you encounter problems, take a look at the [issues](https://github.com/tne-lab/py-behav-box-v2/issues) section of the GitHub and leave a new one if your problem isn't resolved.