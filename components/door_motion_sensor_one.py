from colors import print_gray, print_brown

import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.door_motion_sensor_one import run_door_motion_sensor_one_simulator
from broker_settings import HOSTNAME, PORT


motion_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()


def publisher_task(event, motion_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_motion_batch = motion_batch.copy()
            publish_data_counter = 0
            motion_batch.clear()
        publish.multiple(local_motion_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} motion values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, motion_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def door_motion_sensor_one_callback(settings, status):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

    motion_payload = {
        "measurement": "Motion",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": status
    }

    with counter_lock:
        motion_batch.append(('Motion', json.dumps(motion_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_motion_sensor_one(settings, threads, stop_event):
    if settings['simulated']:
        print_brown("[Door 1] Starting motion sensor simulator")
        door_motion_sensor_one_thread = threading.Thread(target = run_door_motion_sensor_one_simulator, args=(2, door_motion_sensor_one_callback, stop_event, settings))
        door_motion_sensor_one_thread.start()
        threads.append(door_motion_sensor_one_thread)
        print_brown("[Door 1] Motion sensor simulator started")
    else:
        from sensors.door_motion_sensor_one import run_door_motion_sensor_one_loop
        print_brown("[Door 1] Starting motion sensor loop")
        door_motion_sensor_one_thread = threading.Thread(target=run_door_motion_sensor_one_loop, args=(settings, door_motion_sensor_one_callback, stop_event))
        door_motion_sensor_one_thread.start()
        threads.append(door_motion_sensor_one_thread)
        print_brown("[Door 1] Motion sensor loop started")
