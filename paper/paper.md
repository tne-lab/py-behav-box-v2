---
title: 'Pybehave: a hardware agnostic, Python-based framework for controlling behavioral neuroscience experiments'
tags:
  - Python
  - Animal behavior
  - Operant tasks
authors:
  - name: Evan M. Dastin-van Rijn
    orcid: 0000-0000-0000-0000
    affiliation: 1
    corresponding: true
  - name: Joel Nielsen
    affiliation: 1
  - name: Elizabeth M. Sachse
    affiliation: 1
  - name: Christina Li
    affiliation: 1
  - name: Megan E. Mensinger
    affiliation: 1
  - name: Stefanie G. Simpson
    affiliation: 1
  - name: Francesca A. Iacobucci
    affiliation: 1
  - name: David J. Titus
    affiliation: 1
  - name: Alik S. Widge
    affiliation: 1
affiliations:
 - name: Department of Psychiatry and Behavioral Sciences, University of Minnesota Medical Center, Minneapolis, MN 55454, USA
   index: 1
date: 13 August 2017
bibliography: paper.bib
---

# Summary

This work presents our `pybehave` framework for developing behavioral tasks for use in experimental animal neuroscience. 
In contrast to other platforms, `pybehave` is built around a hardware-agnostic and highly object-oriented design philosophy. 
`Pybehave` separates code for task design from specific hardware implementations to streamline development, accessibility, 
and data sharing. This approach, combined with task-specific graphical user interfaces, expedites and simplifies the 
creation and visualization of complex behavioral tasks. User created task definition files can interact with 
hardware-specific source files, both written in Python. Any and all local configuration can be handled separately from 
the underlying task code. 

# Statement of need

Operant animal behavior training and monitoring is fundamental to scientific inquiry across fields [@krakauer_neuroscience_2017]. 
In many cases, a behavior of relevance, or its neural substrate, is best studied through a controlled laboratory task. 
These tasks require tight integration of the hardware components with which animals interact (IR beams, levers, lights, 
food dispensers, etc.) and the overarching software that coordinates these components to elicit desired behaviors. There 
are a plethora of options for systems to facilitate behavioral tasks, from commercial solutions (Panlab, Lafayette Instruments, 
Med Associates) to open-source packages [@akam_open-source_2022; @dastin-van_rijn_oscar_2023; @hwang_nimh_2019] enabling 
a large variety of behavioral paradigms. Many of these systems are designed for the same behavioral paradigms with only 
slight differences in hardware, sensory modalities, or geometry. However, while the actual mechanics of these paradigms 
remain relatively similar, different solutions will often rely on vastly different software interfaces [@cardinal_whisker_2010; 
@lopes_bonsai_2015]. Especially with commercial systems, behavioral tasks are often programmed in proprietary formats. 
This approach significantly raises the barrier to entry, leads to outdated software, and prevents sharing of tasks across labs.

Research in human behavior does not suffer from many of the aforementioned issues. Human behavioral tasks are generally 
run through a graphical interface implemented in a standard programming language like Python [@peirce_psychopy2_2019], 
Javascript [@de_leeuw_jspsych_2015], or Matlab [@brainard_psychophysics_1997]. These tasks are readily compatible with 
most machines and are frequently shared between labs and used across multiple studies [@provenza_honeycomb_2021]. Protocols, 
data, and task code can be easily included in a manuscript and accessed and modified by future researchers. However, unlike 
experiments in animal behavior, human experiments rarely require hardware beyond a monitor and standard input device 
(keyboard/mouse). Instead, most animal platforms, even from open source developers, restrict their software to certain 
types of hardware [@akam_open-source_2022; @hwang_nimh_2019]. For example, `pycontrol` is only compatible with their 
companion microcontroller and input devices and `MonkeyLogic` can only communicate with DAQs manufactured by National 
Instruments. To address these limitations, we developed `pybehave` as a framework for abstracting standard hardware 
components to enable an implementation-independent format for developing and running behavioral tasks. 

# Benefits

`Pybehave` is a complete framework for building and running behavioral neuroscience experiments. It offers the following 
benefits: (1) hardware independence; (2) a flexible, programmatic system for developing tasks; (3) a highly extensible 
graphical interface for configuring and executing tasks; (4) options for task-specific visualization; (5) simultaneous 
control of multiple experiments; (6) options for locally configuring task variables and protocols; and (5) an extensive 
developer API, which allows users to extend the platform with tie-ins for custom hardware, event logging, or software connections.

# Software Design Principles

To ensure flexibility while maintaining low-latency, `pybehave` is optimized through a combination of multiprocessing and 
multithreading along with separation of its features (events, hardware sources, tasks, etc.) into a modular software 
architecture. Additionally, `pybehave` uses two different GUI frameworks (QT and pygame) for user interfacing and task 
visualization/stimulus display respectively (\autoref{fig:framework}).

![Framework diagram showing the information exchange between the `pybehave` threads and processes. The workstation 
process handles the interface and task GUIs. When Tasks are added from the workstation, they are initialized in the task process. 
Each Source with a connection to an external hardware or software system communicates with their `pybehave` equivalent in the 
Task process. All events sent between processes are mediated via inter-process communication over Pipes.\label{fig:framework}](framework.png)

# Tutorials and ongoing usage

A variety of tutorials are included in the repository aimed at all levels of usage, from technicians running tasks or 
analyzing behavioral data to developers aiming to build new tasks or integrate additional hardware. `Pybehave` has already 
been applied to implement a variety of behavioral tasks which have been included in a separate repository for users to 
pull from directly or modify. These tasks are being run in a number of ongoing studies spanning standard operant 
conditioning [@dastin-van_rijn_oscar_2023; @mensinger_462_2023], evoked responses [@sachse_534_2023], and video assays.

# Acknowledgements

Testing of `pybehave` was carried out with substantial support from many members of the Translational Neuroengineering lab. 
Evan Dastin-van Rijn was supported by a National Science Foundation Graduate Research Fellowship under award number 2237827. 
Aspects of the research were supported by grants R01MH123634, R01NS120851, R01NS113804 and R01MH119384, as well as by the 
Minnesota Medical Discovery Team on Addiction and the MnDRIVE Brain Conditions Initiative. The opinions presented herein 
are not those of any funding body.

# References