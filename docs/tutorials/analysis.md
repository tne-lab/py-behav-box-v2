# Basic analysis of pybehave data

In the following tutorial, we will describe the structure of the default pybehave data file that is generated for each 
task by the CSVEventLogger and some methods we recommend for parsing it.

## File structure

By default, every task is initialized with a CSVEventLogger which will serialize all task events in a CSV format. The name 
of the file is the timestamp (in local time) when the task was started. These CSV files have two sections: a header with a 
variety of metadata related to the task followed by a standard CSV table with one row per task event.

### Header

The header is composed of rows of comma separate key-value pairs for each metadata item. Typically, the header will have
five fields: the subject name (Subject), the task name (Task), which chamber the task was run in (Chamber), the absolute 
path to the protocol file if one was provided (Protocol), and the absolute path to the address file if one was provided 
(AddressFile). 

If a SubjectConfiguration widget was added to the chamber, the header will contain an additional set of key-value pairs
for each constant that was overridden in the configuration after a delineating row.

An example header is shown below:

>Subject,test  
Task,SetShift  
Chamber,1  
Protocol,  
AddressFile,C:/Users/Test/Desktop/py-behav/SetShift/AddressFiles/test.py  
SubjectConfiguration  
max_duration,"120"

### Event Table

The main component of the CSV output is the event table which has one row for each Loggable event that occurred during the
task. The table has six columns: the index of the event (Trial), the time in seconds when the event occurred relative to 
the beginning of the task (Time), the type of the event (Type), a numerical representation of the event (Code), a string 
representation of the event (State), and any metadata for the event (Metadata).

The Code and State for each row are pulled from the corresponding LoggerEvent. To see how these fields are populated, look
at the corresponding event's `format` method. The metadata is a string representation of a dictionary. A few example rows
from an event table are shown below:

> 1,4.9600028432905674e-05,StateEnterEvent,0,INITIATION,"{}"  
2,0.9410676000406966,ComponentChangedEvent,1,nose_pokes-0-1,"{'value': True}"  
3,0.9411400000099093,StateExitEvent,0,INITIATION,"{'light_location': False}"  
4,0.9412448999937624,StateEnterEvent,1,RESPONSE,"{'light_location': False}"  
5,1.0427893999731168,ComponentChangedEvent,1,nose_pokes-0-1,"{'value': False}"  
6,1.3491000999929383,ComponentChangedEvent,0,nose_pokes-0-0,"{'value': True}"  
7,1.3491419000783935,StateExitEvent,1,RESPONSE,"{'accuracy': 'correct', 'rule_index': -1}"  
8,1.349303500028327,StateEnterEvent,2,INTER_TRIAL_INTERVAL,"{'accuracy': 'correct', 'rule_index': -1}"  
9,1.442651699995622,ComponentChangedEvent,0,nose_pokes-0-0,"{'value': False}"  
10,8.36388399999123,TimeoutEvent,0,iti_timeout,"{}"  
11,8.364096599980257,StateExitEvent,2,INTER_TRIAL_INTERVAL,"{}"

## Loading pybehave CSVs into Python

Below we provide an example function snippet to read the header and event table into a dictionary and `pandas` dataframe
respectively.

    import os
    import pandas as pd

    def read_pyb(path):
        header = {}
        skip_lines = 0
        
        with open(path) as f:
            for line in f:
                skip_lines += 1
                if line == '\n':
                    break
                elif line == 'SubjectConfiguration\n':
                    header['subject_config'] = {}
                else:
                    pair = line.split(',', 1)
                    if 'subject_config' in header:
                        header['subject_config'][pair[0]] = pair[1][:-1]
                    else:
                        header[pair[0]] = pair[1][:-1]
        
        header['timestamp'] = os.path.split(path)[-1].split('.')[0]
        event_table = pd.read_csv(path, skiprows=skip_lines)
        return event_table, header

Once the event table is loaded as a dataframe, it can be processed using any standard `pandas` indexing operations to translate
it into an application-specific format.

### Splitting metadata into separate columns

One often useful operation when working with `pybehave` data is to split the metadata dictionary into individual columns for
each entry.

    extended_table = pd.concat([event_table, pd.json_normalize(event_table.Metadata.apply(eval))], axis=1)