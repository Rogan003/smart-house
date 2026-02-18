from colors import print_white, print_blue, Colors, print_with_timestamp

import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.door_buzzer_one import run_door_buzzer_one_simulator, run_door_buzzer_one_simulator_loop
from broker_settings import HOSTNAME, PORT


buzzer_batch = []
publish_data_counter = 0
publish_data_limit = 1
counter_lock = threading.Lock()


def publisher_task(event, buzzer_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_buzzer_batch = buzzer_batch.copy()
            publish_data_counter = 0
            buzzer_batch.clear()
        publish.multiple(local_buzzer_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} buzzer values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, buzzer_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def door_buzzer_one_callback(settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_with_timestamp(Colors.BLUE, f"[DB1] active (Door Buzzer 1)", time.strftime('%H:%M:%S', t))

    buzzer_payload = {
        "measurement": "Door Buzzer 1",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": "active"
    }

    with counter_lock:
        buzzer_batch.append(('Door Buzzer 1', json.dumps(buzzer_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_buzzer_one(settings, threads, stop_event):
    if settings['simulated']:
        print_blue("[Door 1] Starting buzzer simulator")
        door_buzzer_one_thread = threading.Thread(target = run_door_buzzer_one_simulator, args=(door_buzzer_one_callback, settings))
        door_buzzer_one_thread.start()
        threads.append(door_buzzer_one_thread)
    else:
        from sensors.door_buzzer_one import run_door_buzzer_one_loop
        print_blue("[Door 1] Starting buzzer loop")
        door_buzzer_one_thread = threading.Thread(target=run_door_buzzer_one_loop, args=(settings, door_buzzer_one_callback, stop_event))
        door_buzzer_one_thread.start()
        threads.append(door_buzzer_one_thread)


def run_door_buzzer_one_continuous(settings, threads, stop_event):
    """Run buzzer in continuous mode that listens for MQTT control messages"""
    if settings['simulated']:
        print_blue("[Door 1] Starting continuous buzzer simulator (MQTT controlled)")
        door_buzzer_one_thread = threading.Thread(target=run_door_buzzer_one_simulator_loop, args=(door_buzzer_one_callback, stop_event, settings))
        door_buzzer_one_thread.start()
        threads.append(door_buzzer_one_thread)
    else:
        from sensors.door_buzzer_one import run_door_buzzer_one_loop
        print_blue("[Door 1] Starting buzzer loop")
        door_buzzer_one_thread = threading.Thread(target=run_door_buzzer_one_loop, args=(settings, door_buzzer_one_callback, stop_event))
        door_buzzer_one_thread.start()
        threads.append(door_buzzer_one_thread)
