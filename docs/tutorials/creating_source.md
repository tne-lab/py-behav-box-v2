# Creating a new source

In the following tutorial, we will show all the basic features that need to be programmed to build a Source from scratch
in pybehave. A user might decide to create a new source if their task or interfacing hardware is not handled by the existing
Sources. If you want to contribute your Source to the wider community, you can create your new class directly in the pybehave
Sources directory and make a pull request. Alternatively, a Sources directory can be made in the Local repository.

## Source overview

Sources are responsible for sending and receiving information to or from external hardware or interfaces. The pybehave Source
class defines a standard framework for implementing these functions. 

## Choosing a base class

There are two primary base classes for sources: Source and ThreadSource. If your source only has to write data then you should
override Source. If your source also has to read data then there are two options: use ThreadSource as a base class which runs two
separate threads one for handling event information from the task and the other for communicating with the hardware or use Source
as a base class but handle reading either when a component is registered or another event is received. Examples of both will be
shown in their relevant sections later in this tutorial.

## The `__init__` method

Each source runs in a separate process from the tasks and workstation. When a new source is created, the `__init__` method will
be called. However, all attributes declared in this method are created in the main process before being transferred to the 
source process by inter process communication. What this means is that all attributes defined in `__init__` should only have
placeholder/default values using [pickleable](https://docs.python.org/3/library/pickle.html) variables. Any permanent connection
to hardware or interfaces should be handled instead in the `initialize` method described later in this tutorial. An example `__init__` 
override for the SerialSource is shown below that declares three new class attributes:

    def __init__(self):
        super(SerialSource, self).__init__()
        self.connections = {}
        self.com_tasks = {}
        self.closing = {}

## `initialize`

In contrast to `__init__`, `initialize` is called in the source process. All connections to hardware and external interfaces
should be implemented in this method. If using the ThreadSource method for reading, the `initialize` method will be called in its own
Thread. As such, polling and event-waiting behavior from the external connection can be handled by this method without interrupting
other event streams. An example of this functionality is shown below for the WhiskerLineSource. This source first opens an
external program and then establishes a connection to it via a socket. Once the connection is established, it waits on messages 
over the socket until the source is closed. All of this functionality is implemented in the `initialize` method without affecting
other source-related processing:

    def initialize(self):
        win32gui.EnumWindows(look_for_program, 'WhiskerServer')
        if not IsWhiskerRunning:
            ws = self.whisker_path
            os.startfile(ws)
            time.sleep(2)
            print("WHISKER server started")
            win32gui.EnumWindows(look_for_program, 'WhiskerServer')
        if IsWhiskerRunning:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.client.connect((self.address, self.port))
            self.client.settimeout(1)
            while not self.closing:
                try:
                    new_data = self.client.recv(4096)
                    self.msg += new_data.decode('UTF-8')
                    if '\n' in self.msg:
                        msgs = self.msg.split('\n')
                        self.msg = msgs[-1]
                    else:
                        msgs = []
                    for msg in msgs[:-1]:
                        if msg.startswith('Event:'):
                            div = msg.split(' ')[1].rindex("_")
                            cid, direction = msg.split(' ')[1][:div], msg.split(' ')[1][div + 1:]
                            self.update_component(cid, direction == "on")
                except socket.timeout:
                    pass
        else:
            self.unavailable()

## `register_component`

The `register_component` method is responsible for establishing a connection between a task component and its hardware or interface
representation via the source. The behavior of this method will of course vary heavily between applications but the method
will always receive the component and relevant metadata as inputs. This method can also be used to set up read/polling threads
if necessary. This is done in the SerialSource where a new serial connection is established and a corresponding thread is started
if one does not exist:

    def register_component(self, component, metadata):
        if component.address not in self.connections:
            self.connections[component.address] = serial.Serial(port=component.address, baudrate=component.baudrate, timeout=1)
            self.closing[component.address] = False
            self.com_tasks[component.address] = threading.Thread(target=self.read, args=[component.address])
            self.com_tasks[component.address].start()

    def read(self, com):
        while not self.closing[com]:
            data = self.connections[com].read_until(expected='\n', size=None)
            if len(data) > 0:
                for comp in self.components.values():
                    if comp.address == com and (comp.get_type() == Component.Type.DIGITAL_INPUT or
                                                comp.get_type() == Component.Type.INPUT or
                                                comp.get_type() == Component.Type.ANALOG_INPUT or
                                                comp.get_type() == Component.Type.BOTH):
                        self.update_component(comp.id, data)
        del self.com_tasks[com]
        del self.closing[com]
        self.connections[com].close()
        del self.connections[com]

## `write_component`

To implement behavior for writing/sending new values to hardware for components, a custom source should override the `write_component`
method. An example of such an override is shown below for the SerialSource which used the pyserial library to mediate the write
to an external serial connection:

    def write_component(self, component_id, msg):
        if hasattr(self.components[component_id], "terminator"):
            term = self.components[component_id].terminator
        else:
            term = ""
        self.connections[self.components[component_id].address].write(bytes(str(msg) + term, 'utf-8'))

## Closing behavior

It's often necessary to close or relinquish external connections. This functionality is accomplished by overriding the `close_component`
or `close_source` methods which will be called when a task is cleared or the source is removed/application is closed respectively.