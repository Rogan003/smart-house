import time
import random

def generate_value():
    if random.randint(0, 100) <= 15:
        print("Door Number One - Opened")

def run_door_button_one_simulator(delay, callback, stop_event):
    while True:
        time.sleep(delay)
        callback()
        generate_value()

        if stop_event.is_set():
            break
