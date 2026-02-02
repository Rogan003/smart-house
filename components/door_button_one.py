from colors import print_gray, print_white

import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.door_button_one import run_door_button_one_simulator
from broker_settings import HOSTNAME, PORT


button_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()


def publisher_task(event, button_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_button_batch = button_batch.copy()
            publish_data_counter = 0
            button_batch.clear()
        publish.multiple(local_button_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} button values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, button_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def door_button_one_callback(settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

    button_press_payload = {
        "measurement": "Door button 1",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "pressed": "TRUE"
    }

    with counter_lock:
        button_batch.append(('Door Buttton 1', json.dumps(button_press_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_door_button_one(settings, threads, stop_event):
    if settings['simulated']:
        print_white("[Door 1] Starting button simulator")
        door_button_one_thread = threading.Thread(target = run_door_button_one_simulator, args=(2, settings, door_button_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)
        print_white("[Door 1] Button simulator started")
    else:
        from sensors.door_button_one import run_door_button_one_loop
        print_white("[Door 1] Starting button loop")
        door_button_one_thread = threading.Thread(target=run_door_button_one_loop, args=(settings, door_button_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)
        print_white("[Door 1] Button loop started")
