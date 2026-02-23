import time
import random

from colors import print_brown


def generate_value(callback, settings):
    # 15% chance to detect motion
    if random.randint(0, 100) <= 15:
        callback(settings, "detected")

def run_door_motion_sensor_two_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break