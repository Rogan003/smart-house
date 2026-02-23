from colors import Colors, print_gray, print_magenta, print_separator

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.door_ultrasonic_sensor_two import run_door_ultrasonic_sensor_two_simulator
from broker_settings import HOSTNAME, PORT


ultrasonic_batch = []
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
            print(f"[DUS2] Live publish error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


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


def door_ultrasonic_sensor_two_callback(distance, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    print()
    print(f"{Colors.MAGENTA}📏 [DUS2] {distance} cm{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    payload = {
        "measurement": "Door Distance Sensor 2",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": distance
    }

    # 1. Non-blocking /live publish (za reakciju servera)
    live_queue.put(('Door Distance Sensor 2/live', json.dumps(payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        ultrasonic_batch.append(('Door Distance Sensor 2/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_ultrasonic_sensor_two(settings, threads, stop_event):
    if settings['simulated']:
        print_magenta("[Door 2] Starting ultrasonic sensor simulator")
        door_ultrasonic_sensor_two_thread = threading.Thread(target = run_door_ultrasonic_sensor_two_simulator, args=(4, door_ultrasonic_sensor_two_callback, stop_event, settings))
        door_ultrasonic_sensor_two_thread.start()
        threads.append(door_ultrasonic_sensor_two_thread)
        print_magenta("[Door 2] Ultrasonic sensor simulator started")
    else:
        from sensors.door_ultrasonic_sensor_two import run_door_ultrasonic_sensor_two_loop
        print_magenta("[Door 2] Starting ultrasonic sensor loop")
        door_ultrasonic_sensor_two_thread = threading.Thread(target=run_door_ultrasonic_sensor_two_loop, args=(settings, 2, door_ultrasonic_sensor_two_callback, stop_event))
        door_ultrasonic_sensor_two_thread.start()
        threads.append(door_ultrasonic_sensor_two_thread)
        print_magenta("[Door 2] Ultrasonic sensor loop started")
