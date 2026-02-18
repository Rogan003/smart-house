import time
import random


def generate_value(callback, settings):
    if random.randint(0, 100) <= 15:
        callback(settings, "detected")

def run_door_motion_sensor_one_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break