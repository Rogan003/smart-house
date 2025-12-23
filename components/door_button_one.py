from simulators.door_button_one import run_door_button_one_simulator
import threading
import time

def door_button_one_callback():
    t = time.localtime()
    print("="*20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")


def run_door_button_one(settings, threads, stop_event):
        if settings['simulated']:
            print("Starting door button 1 simulator")
            door_button_one_thread = threading.Thread(target = run_door_button_one_simulator, args=(2, door_button_one_callback, stop_event))
            door_button_one_thread.start()
            threads.append(door_button_one_thread)
            print("Door button 1 simulator started")
        else:
            from sensors.door_button_one import run_door_button_one_loop
            print("Starting door button 1 loop")
            door_button_one_thread = threading.Thread(target=run_door_button_one_loop, args=(settings["pin"], door_button_one_callback, stop_event))
            door_button_one_thread.start()
            threads.append(door_button_one_thread)
            print("Door button 1 loop started")
