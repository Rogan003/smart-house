import time
import random

from colors import print_white


def generate_value(callback, settings):
    if random.randint(0, 100) <= 15:
        callback(settings)
        print_white("[DS2] Door opened (Door Sensor 2)")

def run_door_button_two_simulator(delay, settings, callback, stop_event):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break
