import time
import sys
sys.path.append('..')
from buzzer_controller import buzzer_controller


def buzz(callback, settings):
    callback(settings)

def run_door_buzzer_one_simulator(callback, settings):
    buzz(callback, settings)

def run_door_buzzer_one_simulator_loop(callback, stop_event, settings):
    """Continuous buzzer simulator that buzzes while buzzer_controller is active"""
    while not stop_event.is_set():
        if buzzer_controller.is_active():
            callback(settings)
            time.sleep(0.5)  # buzz interval while active
        else:
            time.sleep(0.1)