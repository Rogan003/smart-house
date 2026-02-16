import time
import random

from colors import print_magenta


def generate_value(callback, settings):
    distance = random.uniform(10, 100)
    callback(distance, settings)
    print_magenta(f"[Door 1] - Distance: {distance} cm (ultrasonic sensor)")

def run_door_ultrasonic_sensor_one_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break