from colors import Colors, print_gray, print_brown, print_separator

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.door_motion_sensor_two import run_door_motion_sensor_two_simulator
from broker_settings import HOSTNAME, PORT


motion_batch = []
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
            print(f"[DPIR2] error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


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


def door_motion_sensor_two_callback(settings, status):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    emoji = "🚶" if status == "detected" else "⬜"
    color = Colors.BROWN if status == "detected" else Colors.GRAY
    print()
    print(f"{color}{emoji} [DPIR2] {status}{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    payload = {
        "measurement": "Door Motion Sensor 2",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": status
    }

    # send to live topic
    live_queue.put(('Door Motion Sensor 2/live', json.dumps(payload)))

    # add to batch
    with counter_lock:
        motion_batch.append(('Door Motion Sensor 2/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_motion_sensor_two(settings, threads, stop_event):
    if settings['simulated']:
        print_brown("[Door 2] Starting motion sensor simulator")
        door_motion_sensor_two_thread = threading.Thread(target = run_door_motion_sensor_two_simulator, args=(2, door_motion_sensor_two_callback, stop_event, settings))
        door_motion_sensor_two_thread.start()
        threads.append(door_motion_sensor_two_thread)
        print_brown("[Door 2] Motion sensor simulator started")
    else:
        from sensors.door_motion_sensor_two import run_door_motion_sensor_two_loop
        print_brown("[Door 2] Starting motion sensor loop")
        door_motion_sensor_two_thread = threading.Thread(target=run_door_motion_sensor_two_loop, args=(settings, door_motion_sensor_two_callback, stop_event))
        door_motion_sensor_two_thread.start()
        threads.append(door_motion_sensor_two_thread)
        print_brown("[Door 2] Motion sensor loop started")
