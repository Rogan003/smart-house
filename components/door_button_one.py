from colors import print_gray, print_white

import threading
import time

from simulators.door_button_one import run_door_button_one_simulator


def door_button_one_callback():
    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

def run_door_button_one(settings, threads, stop_event):
    if settings['simulated']:
        print_white("[Door 1] Starting button simulator")
        door_button_one_thread = threading.Thread(target = run_door_button_one_simulator, args=(2, door_button_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)
        print_white("[Door 1] Button simulator started")
    else:
        from sensors.door_button_one import run_door_button_one_loop
        print_white("[Door 1] Starting button loop")
        door_button_one_thread = threading.Thread(target=run_door_button_one_loop, args=(settings["pin"], door_button_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)
        print_white("[Door 1] Button loop started")
