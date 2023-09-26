import json
import numpy as np
from collections import defaultdict
import os



def load_json_file(filepath):
    with open(filepath, "r", encoding="utf8") as f:
        return json.load(f)


def get_instant_events(events):
    return [e for e in events if 'cat' in e and e['cat'].lower() == 'instant']


def group_by_trace_id(events):
    grouped_events = defaultdict(list)

    for event in events:
        if 'args' in event and 'trace_id' in event['args']:
            trace_id = event['args']['trace_id']
            grouped_events[trace_id].append(event)

    return grouped_events

if __name__ == '__main__':
    # Load JSON data from a file
    file_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', 'py-behav', 'profiling', 'result.json') 
    json_data = load_json_file(file_path)

    instant_events = get_instant_events(json_data.get('traceEvents', []))

    print(f"Found {len(instant_events)} instant events")

    by_name = {}

    for event in instant_events:
        if (event["name"] in by_name):
            by_name[event["name"]].append(event)
        else:
            by_name[event["name"]] = [event]

    grouped_events = group_by_trace_id(instant_events)

    latencies_by_type = {}

    for trace_id, events in grouped_events.items():
        events.sort(key=lambda event: event['ts'])
        
        # Assuming the events list is not empty, get the timestamp of the first event
        first_event = events[0]
        first_timestamp = first_event['ts']
        
        for i in range(1, len(events)):  # Start from 1 as we are comparing with the 0th element
            current_event = events[i]
            current_timestamp = current_event['ts']
            
            latency_milliseconds = (current_timestamp - first_timestamp) / 1000

            if "name" in current_event["args"]:
                key = first_event["name"] + "_to_" + current_event["name"] + "_type_" + current_event["args"]["name"]
                if (key not in latencies_by_type):
                    latencies_by_type[key] = [latency_milliseconds]
                else:
                    latencies_by_type[key].append(latency_milliseconds)

    for k, v in latencies_by_type.items():
        print(f"Mean latency for {k}: {np.mean(v)}")