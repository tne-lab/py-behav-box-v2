# Creating a new task sequence

In the following tutorial, we will show all the basic features that need to be programmed to build a TaskSequence from scratch. It is recommended to start with the [creating a task tutorial](/tutorials/creating_task) as this tutorial will build on the concepts outlined there. See the [TaskSequence](/task_sequences) documentation for a more thorough explanation of TaskSequences.

## TaskSequence overview



For this tutorial we'll create a sequence of Tasks that run consecutively. The underlying Tasks we'll be running are the Raw task, which has no behavioral component, and the BarPress task created in the task tutorial. The sequence will first run the Raw task, then the BarPress, then the Raw task again. The Raw task can be found in the [TNEL all-tasks Github repository](https://github.com/tne-lab/all-tasks/tree/event-based)

To start, create a file named BarPressSequence.py within the `Local/Tasks` folder.

## Imports

We will be using the following imports in the process of developing this Task:

    from enum import Enum
    from Events import PybEvents
    from Tasks.TaskSequence import TaskSequence
    from .BarPress import BarPress 
    from .Raw import Raw
    

## Subclassing

TasksSequences, like most features of pybehave, are objects. All TasksSequences extend the base TaskSequence class, which itself extends the base Task class. These extensions handle most of the lower-level
behavior while exposing simpler methods to the user. 

    class BarPressSequence(TaskSequence):
        """@DynamicAttrs"""

## States

In TaskSequences, each member of the States enum represents one run of a particular Task. The names of these entries do not need to match the name of the Task itself. In this case, we'll distinguish the two instances of the Raw task by naming them `PRE_RAW` and `POST_RAW`.

    class States(Enum):
        PRE_RAW = 0
        BAR_PRESS = 1
        POST_RAW = 2

The names given for each state in this enum will become relevant later when we need to program the behavior for each State.


## get_tasks
All TaskSequences must define which Tasks are being run through the `get_tasks` method. This method returns the types of all Tasks included in the sequence. In this case it looks like: 

    @staticmethod
    def get_tasks():
        return [BarPress, Raw]

## get_constants
The `get_constants` method is used to define sequence-level constants. It can also contain [protocol files](/protocols_addressfiles#protocols) to be used for the individual Tasks in the sequence. In this case, we will use the default constants for each task by providing `None`, however, one can provide a specific file path here to change which protocol is run for the tasks.

    @staticmethod
    def get_constants():
        return {
            'pre_raw_protocol': None,
            'bar_press_protocol': None,
            'post_raw_protocol': None
        }

## init_state and init_sequence
Similar to Tasks, we need to override the `init_state` method to declare which entry in the States enum is first:

    def init_state(self):
        return self.States.PRE_RAW

Additionally, we must override the `init_sequence` method which returns a tuple containing the initial Task class and the initial protocol.

    def init_sequence(self):
        return Raw, self.pre_raw_protocol

## all_states
In this case, we don't need to handle any events in the TaskSequence `all_states` method, so we can just return `False` which indicates the event wasn't handled.

    def all_states(self, event):
        return False


## state_methods

Each state method of a TaskSequence must at minimum provide logic on how to proceed when the current Task is complete. This can be done using the `switch_task` method. When the `PRE_RAW` state finishes, we want to switch to the bar press task.

    def PRE_RAW(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.switch_task(BarPress, self.States.BAR_PRESS, self.bar_press_protocol, event.metadata)
            return True
        return False

Similarly, the `BAR_PRESS` method will transition to the `POST_RAW` state

    def BAR_PRESS(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.switch_task(Raw, self.States.BAR_PRESS, self.post_raw_protocol, event.metadata)
            return True
        return False

Finally, when the `POST_RAW` Task finishes, we can set the `complete` property to `True` to indicate the sequence is finished.

    def POST_RAW(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.complete = True
            return True
        return False

## GUI

TaskSequences will automatically display the GUI of the current Task being run, however, we can add additional elements to the GUI that will remain throughout the entire sequence lifetime. In this example, we'll simply add a timer that displays how long the sequence has been running.

Create a file named BarPressSequenceGUI.py in the Local/GUIs folder.

### Imports

We will be using the following imports in the GUI:

    from Elements.InfoBoxElement import InfoBoxElement
    from Events import PybEvents
    from GUIs.SequenceGUI import SequenceGUI


### Subclassing
GUIs for TaskSequences must be subclasses of the `TaskSequenceGUI` class. The `TaskSequenceGUI` class inherits from the [GUI](/guis) class which means it includes all of the convenience variables and functions such as the `log_gui_event` function and the `time_elapsed` variable.

    class BarPressSequenceGUI(SequenceGUI):
        """@DynamicAttrs"""

### initialize

The `initialize` function should create and return any elements used by the sequence GUI. In this case, we'll create an info box displaying the time elapsed and position it near the bottom of the screen.

    def initialize(self):
        self.session_time_box = InfoBoxElement(self, 200, 700, 100, 30, "SESSION TIME", 'BOTTOM', ['0'], f_size=28)
        return [self.session_time_box]

### handle_event

Similar to normal GUIs, we must include a `handle_event` function. The only thing we need to do in this function is update the time displayed in our info box. We can take advantage of the `time_elapsed` variable here.

    def handle_event(self, event: PybEvents.PybEvent):
        super().handle_event(event)
        self.session_time_box.set_text(str(round(self.time_elapsed / 60, 2)))




## Additional functionality

This is now a functioning TaskSequence that can be run, however there are additional features of SequenceGUIs that can be utilized if desired. TaskSequences can contain their own components that are independent of individual Task components. For example, we cant send a signal to some other hardware or software when each of the Tasks completes. In this example, we'll simply turn a light on for one second when the Task switches.

### Additional imports

Add the following import to the BarPressSequence.py file

    from Components.TimedToggle import TimedToggle

Add the following import to the BarPressSequenceGUI.py file

    from Elements.CircleLightElement import CircleLightElement

### Task changes

TaskSequences can define sequence level components by declaring a `get_sequence_components` method which works similarly to a Task's `get_components` method.

Add the following to the `BarPressSequence` class:

    @staticmethod
    def get_sequence_components():
        return {
            'task_switch_light': [TimedToggle]
        }


Previously, we didn't handle any events in the `all_states` method. For this extension though, we want to activate the light no matter which Task is running. We can modify the `all_states` method as follows to toggle the light whenever a `TaskCompleteEvent` occurs.

    def all_states(self, event):
        if isinstance(event, PybEvents.TaskCompleteEvent):
            self.task_switch_light.toggle(1.0)
        return False

Note that we still return False here since the individual state methods also handle the `TaskCompleteEvents`. We want this event to pass through both the `all_states` method and the individual state methods.


### GUI changes

Modify the `initialize` method of the `BarPressSequenceGUI` to add a `CircleLightElement` to indicate the status of the light in the GUI.

    def initialize(self):
        self.session_time_box  = InfoBoxElement(self, 200, 700, 100, 30, "SESSION TIME", 'BOTTOM', ['0'], f_size=28)
        self.task_switch_element = CircleLightElement(self, 100, 700, 25, comp=self.task_switch_light)
        return [self.time_elapsed_element, self.session_time_box]


Here, we link the light element to the sequence component we just added to the task through the `comp` argument. Now when we run the Task, the light will toggle for one second each time the Task changes. If we wanted to hook this up to some external hardware or software, we could use an [address file](/protocols_addressfiles) to link it to a [source](/sources).