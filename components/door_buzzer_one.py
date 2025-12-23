import threading
import time

from colors import print_gray
from simulators.door_buzzer_one import run_door_buzzer_one_simulator


def door_buzzer_one_callback():
    t = time.localtime()
    print_gray("="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")


def run_door_buzzer_one(settings, threads, stop_event):
    if settings['simulated']:
        print_gray("Starting door buzzer 1 simulator")
        door_button_one_thread = threading.Thread(target = run_door_buzzer_one_simulator, args=(door_buzzer_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)

    else:
        from sensors.door_buzzer_one import run_door_buzzer_one_loop
        print_gray("Starting door buzzer 1 loop")
        door_button_one_thread = threading.Thread(target=run_door_buzzer_one_loop, args=(settings["pin"], door_buzzer_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)
