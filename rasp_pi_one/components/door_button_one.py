from colors import print_white, Colors, print_with_timestamp

import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.door_button_one import run_door_button_one_simulator
from broker_settings import HOSTNAME, PORT


button_batch = []
publish_data_counter = 0
publish_data_limit = 1
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
        print(f'[DS1] Published {publish_data_limit} door sensor values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, button_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def door_button_one_callback(settings, value="TRUE"):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    status = "OPEN" if value == "TRUE" else "CLOSED"
    print_with_timestamp(Colors.CYAN, f"[DS1] {status} (Door Sensor 1)", time.strftime('%H:%M:%S', t))

    button_press_payload = {
        "measurement": "Door button 1",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    with counter_lock:
        button_batch.append(('Door Button 1', json.dumps(button_press_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_door_button_one(settings, threads, stop_event):
    if settings['simulated']:
        print_white("[DS1] Starting simulator (Door Sensor 1)")
        door_button_one_thread = threading.Thread(target = run_door_button_one_simulator, args=(2, settings, door_button_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)
        print_white("[DS1] Simulator started (Door Sensor 1)")
    else:
        from sensors.door_button_one import run_door_button_one_loop
        print_white("[DS1] Starting loop (Door Sensor 1)")
        door_button_one_thread = threading.Thread(target=run_door_button_one_loop, args=(settings, door_button_one_callback, stop_event))
        door_button_one_thread.start()
        threads.append(door_button_one_thread)
        print_white("[DS1] Loop started (Door Sensor 1)")
