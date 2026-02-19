import time
from kitchen_timer import kitchen_timer

def run_kitchen_segment_display_simulator(callback, stop_event, settings):
    show_zero = True
    while not stop_event.is_set():
        time.sleep(1)
        if kitchen_timer.is_blinking():
            if show_zero:
                callback(settings, "0000")
            else:
                callback(settings, "    ")
            show_zero = not show_zero
        else:
            current_val = kitchen_timer.decrement()
            callback(settings, current_val)
            show_zero = True
