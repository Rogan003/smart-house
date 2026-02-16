import time
from kitchen_timer import kitchen_timer

def run_kitchen_segment_display_simulator(callback, stop_event, settings):
    while not stop_event.is_set():
        time.sleep(1)
        current_val = kitchen_timer.decrement()
        callback(settings, current_val)
