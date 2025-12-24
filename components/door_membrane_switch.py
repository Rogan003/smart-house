from colors import print_gray, print_green

import threading
import time

from simulators.door_membrane_switch import run_door_membrane_switch_simulator


def door_membrane_switch_callback(key):
    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}, Key '{key}' pressed")

def run_door_membrane_switch(settings, threads, stop_event, row, col):
    if settings['simulated']:
        print_green("[Door 1] Starting membrane switch simulator")
        door_membrane_switch_thread = threading.Thread(target = run_door_membrane_switch_simulator, args=(0.2, door_membrane_switch_callback, stop_event, row, col))
        door_membrane_switch_thread.start()
        threads.append(door_membrane_switch_thread)
    else:
        from sensors.door_membrane_switch import run_door_membrane_switch_loop
        print_green("[Door 1] Starting membrane switch loop")
        door_membrane_switch_thread = threading.Thread(target=run_door_membrane_switch_loop, args=(settings["pins"], door_membrane_switch_callback, stop_event))
        door_membrane_switch_thread.start()
        threads.append(door_membrane_switch_thread)
