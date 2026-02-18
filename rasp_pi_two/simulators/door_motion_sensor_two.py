import time
import random

from colors import print_brown


def generate_value(callback, settings):
    if random.randint(0, 100) <= 15:
        callback(settings, "detected")
        print_brown("[DPIR2] Motion Detected (Door PIR Sensor 2)")

def run_door_motion_sensor_two_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break