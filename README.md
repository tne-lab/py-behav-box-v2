# Profiling branch

Uses the [Viztracer](https://viztracer.readthedocs.io/en/latest/index.html) library to time function calls and inter-process latency



### Instructions
Follow the Viztracer installation guide and run py-behav with the modified bat file

By default this will save a json file named `result.json` in your `py-behav/profiling` directory.


To view the trace file run:
```
vizviewer result.json
# OR
python3 -m viztracer.viewer result.json
```

### Events
I added a UUID field, `trace_id` to each event in order to track it through all processes. This adds around 100-150 microseconds of latency and can be taken out if it's not needed for whatever latency you're measuring.

See the Viztracer docs for a thorough guide, but there are comments like this throughout the code:
```
# !viztracer: log_instant("tp-gui-send", scope='g', args={"trace_id": str(event.trace_id), "name": type(event).__name__})
```

This comment logs the timestamp within the trace file, along with any arguments. 

Can also log without adding any args to affect the timing less
```
!viztracer: log_instant("sample-event-name")
``````


### Analyzing Event Latency
The analyze-custom-events.py script takes in the result.json file and calculates the latencies of events as they move throughout different processes. This version calculates the mean latency for each leg in each event's journey and groups them by event type. 