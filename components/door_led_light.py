from colors import print_gray, print_yellow

import threading
import time

from simulators.door_led_light import run_door_led_light_simulator


def door_led_light_callback():
    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

def run_door_led_lights(settings, threads, stop_event):
    if settings['simulated']:
        print_yellow("[Door 1] Starting LED light simulator")
        door_led_light_thread = threading.Thread(target = run_door_led_light_simulator, args=(door_led_light_callback,))
        door_led_light_thread.start()
        threads.append(door_led_light_thread)
    else:
        from sensors.door_led_light import run_door_led_light_loop
        print_yellow("[Door 1] Starting LED light loop")
        door_led_light_thread = threading.Thread(target=run_door_led_light_loop, args=(settings["pin"], door_led_light_callback, stop_event))
        door_led_light_thread.start()
        threads.append(door_led_light_thread)
