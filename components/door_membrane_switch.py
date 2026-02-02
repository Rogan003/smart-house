from colors import print_gray, print_green

import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.door_membrane_switch import run_door_membrane_switch_simulator
from broker_settings import HOSTNAME, PORT


membrane_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()


def publisher_task(event, membrane_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_membrane_batch = membrane_batch.copy()
            publish_data_counter = 0
            membrane_batch.clear()
        publish.multiple(local_membrane_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} membrane values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, membrane_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def door_membrane_switch_callback(key, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}, Key '{key}' pressed")

    membrane_payload = {
        "measurement": "Door Membrane Switch",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": key
    }

    with counter_lock:
        membrane_batch.append(('Door Membrane Switch', json.dumps(membrane_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_membrane_switch(settings, threads, stop_event, row, col):
    if settings['simulated']:
        print_green("[Door 1] Starting membrane switch simulator")
        door_membrane_switch_thread = threading.Thread(target = run_door_membrane_switch_simulator, args=(0.2, door_membrane_switch_callback, stop_event, row, col, settings))
        door_membrane_switch_thread.start()
        threads.append(door_membrane_switch_thread)
    else:
        from sensors.door_membrane_switch import run_door_membrane_switch_loop
        print_green("[Door 1] Starting membrane switch loop")
        door_membrane_switch_thread = threading.Thread(target=run_door_membrane_switch_loop, args=(settings, door_membrane_switch_callback, stop_event))
        door_membrane_switch_thread.start()
        threads.append(door_membrane_switch_thread)
