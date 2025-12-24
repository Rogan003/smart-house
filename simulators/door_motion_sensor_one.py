import time
import random

from colors import print_brown


def generate_value(callback):
    if random.randint(0, 100) <= 15:
        callback()
        print_brown("[Door 1] - Motion Detected")

def run_door_motion_sensor_one_simulator(delay, callback, stop_event):
    while True:
        time.sleep(delay)
        generate_value(callback)

        if stop_event.is_set():
            break