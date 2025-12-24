import time
import random

from colors import print_white


def generate_value(callback):
    if random.randint(0, 100) <= 15:
        callback()
        print_white("[Door 1] - Door opened")

def run_door_button_one_simulator(delay, callback, stop_event):
    while True:
        time.sleep(delay)
        generate_value(callback)

        if stop_event.is_set():
            break
