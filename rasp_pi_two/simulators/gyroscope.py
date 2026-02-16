import time
import random

def generate_values():
    while True:
        # Accelerometer data
        accel = [random.uniform(-2, 2) for _ in range(3)]
        # Gyroscope data
        gyro = [random.uniform(-250, 250) for _ in range(3)]
        yield accel, gyro

def run_gyroscope_simulator(delay, callback, stop_event, settings):
    gen = generate_values()
    while not stop_event.is_set():
        time.sleep(delay)
        accel, gyro = next(gen)
        callback(accel, gyro, settings)
