import time
import random

from colors import print_magenta


def generate_value(callback, settings):
    distance = round(random.uniform(10, 100), 2)
    callback(distance, settings)
    print_magenta(f"[Door 2] - Distance: {distance} cm (ultrasonic sensor)")

def run_door_ultrasonic_sensor_two_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break