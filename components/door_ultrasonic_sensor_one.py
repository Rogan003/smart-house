from colors import print_gray

import threading
import time

from simulators.door_ultrasonic_sensor_one import run_door_ultrasonic_sensor_one_simulator


def door_ultrasonic_sensor_one_callback(distance):
    t = time.localtime()
    print_gray("\n" + "=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}, Distance: {distance} cm")

def run_door_ultrasonic_sensor_one(settings, threads, stop_event):
    if settings['simulated']:
        print_gray("Starting door ultrasonic sensor 1 simulator")
        door_ultrasonic_sensor_one_thread = threading.Thread(target = run_door_ultrasonic_sensor_one_simulator, args=(2, door_ultrasonic_sensor_one_callback, stop_event))
        door_ultrasonic_sensor_one_thread.start()
        threads.append(door_ultrasonic_sensor_one_thread)
    else:
        from sensors.door_ultrasonic_sensor_one import run_door_ultrasonic_sensor_one_loop
        print_gray("Starting door ultrasonic sensor 1 loop")
        door_ultrasonic_sensor_one_thread = threading.Thread(target=run_door_ultrasonic_sensor_one_loop, args=(settings['pin_trig'], settings['pin_echo'], 2, door_ultrasonic_sensor_one_callback, stop_event))
        door_ultrasonic_sensor_one_thread.start()
        threads.append(door_ultrasonic_sensor_one_thread)
