import time
import random


def generate_value(callback, settings):
    # 30% chance to detect motion (increased for more frequent entry/exit simulation)
    if random.randint(0, 100) <= 30:
        callback(settings, "detected")

def run_door_motion_sensor_one_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break