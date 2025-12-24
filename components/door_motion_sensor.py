from colors import print_gray

import threading
import time

from simulators.door_motion_sensor import run_door_motion_sensor_one_simulator


def door_motion_sensor_one_callback():
    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")


def run_door_motion_sensor_one(settings, threads, stop_event):
        if settings['simulated']:
            print_gray("Starting door motion sensor 1 simulator")
            door_motion_sensor_one_thread = threading.Thread(target = run_door_motion_sensor_one_simulator, args=(2, door_motion_sensor_one_callback, stop_event))
            door_motion_sensor_one_thread.start()
            threads.append(door_motion_sensor_one_thread)
            print_gray("Door motion sensor 1 simulator started")
        else:
            from sensors.door_motion_sensor import run_door_motion_sensor_one_loop
            print_gray("Starting door motion sensor 1 loop")
            door_motion_sensor_one_thread = threading.Thread(target=run_door_motion_sensor_one_loop, args=(settings["pin"], door_motion_sensor_one_callback, stop_event))
            door_motion_sensor_one_thread.start()
            threads.append(door_motion_sensor_one_thread)
            print_gray("Door motion sensor 1 loop started")
