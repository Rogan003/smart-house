from colors import print_gray, print_magenta

import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.door_ultrasonic_sensor_one import run_door_ultrasonic_sensor_one_simulator
from broker_settings import HOSTNAME, PORT


ultrasonic_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()


def publisher_task(event, ultrasonic_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_ultrasonic_batch = ultrasonic_batch.copy()
            publish_data_counter = 0
            ultrasonic_batch.clear()
        publish.multiple(local_ultrasonic_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} ultrasonic values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ultrasonic_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def door_ultrasonic_sensor_one_callback(distance, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}, Distance: {distance} cm")

    ultrasonic_payload = {
        "measurement": "Distance",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": distance
    }

    with counter_lock:
        ultrasonic_batch.append(('Distance', json.dumps(ultrasonic_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_ultrasonic_sensor_one(settings, threads, stop_event):
    if settings['simulated']:
        print_magenta("[Door 1] Starting ultrasonic sensor simulator")
        door_ultrasonic_sensor_one_thread = threading.Thread(target = run_door_ultrasonic_sensor_one_simulator, args=(5, door_ultrasonic_sensor_one_callback, stop_event, settings))
        door_ultrasonic_sensor_one_thread.start()
        threads.append(door_ultrasonic_sensor_one_thread)
        print_magenta("[Door 1] Ultrasonic sensor simulator started")
    else:
        from sensors.door_ultrasonic_sensor_one import run_door_ultrasonic_sensor_one_loop
        print_magenta("[Door 1] Starting ultrasonic sensor loop")
        door_ultrasonic_sensor_one_thread = threading.Thread(target=run_door_ultrasonic_sensor_one_loop, args=(settings, 2, door_ultrasonic_sensor_one_callback, stop_event))
        door_ultrasonic_sensor_one_thread.start()
        threads.append(door_ultrasonic_sensor_one_thread)
        print_magenta("[Door 1] Ultrasonic sensor loop started")
