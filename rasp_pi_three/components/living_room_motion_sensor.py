from colors import Colors, print_gray, print_brown, print_separator

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.living_room_motion_sensor import run_living_room_motion_sensor_simulator
from broker_settings import HOSTNAME, PORT


motion_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

# Queue for non-blocking /live publishing
live_queue = queue.Queue()


def live_publisher_task():
    """Daemon thread for non-blocking /live message publishing"""
    while True:
        try:
            topic, payload = live_queue.get()
            publish.single(topic, payload, hostname=HOSTNAME, port=PORT)
            live_queue.task_done()
        except Exception as e:
            print(f"[DPIR3] Live publish error: {e}")

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


def living_room_motion_sensor_callback(settings, status):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    emoji = "🚶" if status == "detected" else "⬜"
    color = Colors.BROWN if status == "detected" else Colors.GRAY
    print()
    print(f"{color}{emoji} [DPIR3] {status}{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    payload = {
        "measurement": "Living Room Motion Sensor",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": status
    }

    # 1. Non-blocking /live publish (za reakciju servera)
    live_queue.put(('Living Room Motion Sensor/live', json.dumps(payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        motion_batch.append(('Living Room Motion Sensor/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_living_room_motion_sensor(settings, threads, stop_event):
    if settings['simulated']:
        print_brown("[Living Room] Starting motion sensor simulator")
        living_room_motion_sensor_thread = threading.Thread(target = run_living_room_motion_sensor_simulator, args=(4, living_room_motion_sensor_callback, stop_event, settings))
        living_room_motion_sensor_thread.start()
        threads.append(living_room_motion_sensor_thread)
        print_brown("[Living Room] Motion sensor simulator started")
    else:
        from sensors.living_room_motion_sensor import run_living_room_motion_sensor_loop
        print_brown("[Living Room] Starting motion sensor loop")
        living_room_motion_sensor_thread = threading.Thread(target=run_living_room_motion_sensor_loop, args=(settings, living_room_motion_sensor_callback, stop_event))
        living_room_motion_sensor_thread.start()
        threads.append(living_room_motion_sensor_thread)
        print_brown("[Living Room] Motion sensor loop started")
