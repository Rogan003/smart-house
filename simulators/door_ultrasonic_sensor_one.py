import random
import time

from colors import print_magenta


def generate_value(callback):
    distance = random.uniform(10, 100)
    callback(distance)
    print_magenta(f"Door Number One - Distance: {distance} cm")

def run_door_ultrasonic_sensor_one_simulator(delay, callback, stop_event):
    while True:
        generate_value(callback)

        if stop_event.is_set():
            break
        time.sleep(delay)