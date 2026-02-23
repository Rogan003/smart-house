from colors import print_white, Colors, print_with_timestamp

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.door_button_one import run_door_button_one_simulator
from broker_settings import HOSTNAME, PORT


button_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

# Queue for non-blocking /live publishing
live_queue = queue.Queue()


def live_publisher_task():
    while True:
        try:
            topic, payload = live_queue.get()
            publish.single(topic, payload, hostname=HOSTNAME, port=PORT)
            live_queue.task_done()
        except Exception as e:
            print(f"[DS1] error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, button_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_button_batch = button_batch.copy()
            publish_data_counter = 0
            button_batch.clear()
        publish.multiple(local_button_batch, hostname=HOSTNAME, port=PORT)
        print(f'[DS1] Published {len(local_button_batch)} door sensor values (batch)')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, button_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def door_button_one_callback(settings, value="TRUE"):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    status = "OPEN" if value == "TRUE" else "CLOSED"
    emoji = "🚪" if value == "TRUE" else "🔒"
    print_with_timestamp(Colors.CYAN, f"{emoji} [DS1] {status} (Door Sensor 1)", time.strftime('%H:%M:%S', t))

    payload = {
        "measurement": "Door button 1",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    # send to live topic
    live_queue.put(('Door Button 1/live', json.dumps(payload)))

    # add to batch
    with counter_lock:
        button_batch.append(('Door Button 1/batch', json.dumps(payload), 0, True))
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
