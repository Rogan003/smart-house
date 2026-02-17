import time
from rgb_controller import rgb_controller

def run_bedroom_rgb_simulator(callback, stop_event, settings):
    def on_color_change(color):
        callback(color, settings)

    # Initial state
    on_color_change(rgb_controller.get_color())
    
    # Register callback in controller to react immediately
    rgb_controller.set_callback(on_color_change)

    while not stop_event.is_set():
        time.sleep(0.1)
