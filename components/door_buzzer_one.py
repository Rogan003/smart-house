from colors import print_gray, print_blue

import threading
import time

from simulators.door_buzzer_one import run_door_buzzer_one_simulator


def door_buzzer_one_callback():
    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

def run_door_buzzer_one(settings, threads, stop_event):
    if settings['simulated']:
        print_blue("[Door 1] Starting buzzer simulator")
        door_buzzer_one_thread = threading.Thread(target = run_door_buzzer_one_simulator, args=(door_buzzer_one_callback,))
        door_buzzer_one_thread.start()
        threads.append(door_buzzer_one_thread)
    else:
        from sensors.door_buzzer_one import run_door_buzzer_one_loop
        print_blue("[Door 1] Starting buzzer loop")
        door_buzzer_one_thread = threading.Thread(target=run_door_buzzer_one_loop, args=(settings["pin"], door_buzzer_one_callback, stop_event))
        door_buzzer_one_thread.start()
        threads.append(door_buzzer_one_thread)
