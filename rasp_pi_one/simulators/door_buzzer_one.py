import time
import sys
sys.path.append('..')
from buzzer_controller import buzzer_controller


def buzz(callback, settings):
    callback(settings)

def run_door_buzzer_one_simulator(callback, settings):
    buzz(callback, settings)

def run_door_buzzer_one_simulator_loop(callback, stop_event, settings):
    """Continuous buzzer simulator that reacts to buzzer_controller state"""
    def on_buzzer_change(active):
        if active:
            callback(settings)

    buzzer_controller.set_callback(on_buzzer_change)
    
    # initial state check
    if buzzer_controller.is_active():
        on_buzzer_change(True)

    while not stop_event.is_set():
        time.sleep(0.1)