import time
import random

from colors import print_white


def generate_value(callback, settings):
    if random.randint(0, 100) <= 15:
        callback(settings)
        print_white("[Door 1] - Door opened")

def run_door_button_one_simulator(delay, settings, callback, stop_event):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break
