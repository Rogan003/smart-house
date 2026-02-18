import time
import random


def generate_value(callback, settings):
    distance = round(random.uniform(10, 100), 2)
    callback(distance, settings)

def run_door_ultrasonic_sensor_one_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break