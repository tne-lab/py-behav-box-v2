# Local configuration with Protocols and AddressFiles

## Overview

Pybehave allows users to alter task functionality through two types of local files that can be loaded at runtime: Protocols and AddressFiles. 
Protocols are local Python files that can be processed to override default values for task constants. These constants can be used
to control a variety of task behavior including trial timing and order, types of trials to include, or general rules for 
task progression. Together, constants reduce the number of similar tasks that have to be written and simplify basic variation
in tasks. AddressFiles are local CSV files that indicate which [Sources]() are related to each [Component](), any necessary hardware
addresses, and optional metadata. AddressFiles simplify the process of running the same task on a variety of hardware without
editing the underlying task files.

## Protocols

Protocols are written as Python files that are executed at runtime to modify task constants. Tasks can have any number of protocols
to alter all or a subset of constants. Protocol files can define any necessary imports, variables, or functions; the only
requirement is that they define a dictionary called `protocol`. Each item in `protocol` must correspond to a constant defined
by the task's `get_constants` method with a new value to replace the pre-existing one. An example protocol is shown below:

    import math

    protocol = {'inter_trial_interval': 3,
            'response_duration': 6,
            'reward_amount': 3**2*math.pi}

Protocols can be loaded from any directory, but we recommend saving them at *Desktop/py-behav-v2/TASK_NAME/Protocols*.

## AddressFiles

