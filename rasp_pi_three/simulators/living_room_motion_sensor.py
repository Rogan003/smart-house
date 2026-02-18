import time
import random

from colors import print_brown


def generate_value(callback, settings):
    if random.randint(0, 100) <= 15:
        callback(settings, "detected")
        print_brown("[RPIR1] Motion Detected (Living Room PIR Sensor)")

def run_living_room_motion_sensor_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break