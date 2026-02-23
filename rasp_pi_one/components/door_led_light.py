from colors import print_white, print_yellow, Colors, print_with_timestamp

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.door_led_light import run_door_led_light_simulator
from broker_settings import HOSTNAME, PORT


led_batch = []
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
            print(f"[DL1] Live publish error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, led_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_led_batch = led_batch.copy()
            publish_data_counter = 0
            led_batch.clear()
        publish.multiple(local_led_batch, hostname=HOSTNAME, port=PORT)
        print(f'[DL1] Published {publish_data_limit} led values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, led_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def door_led_light_callback(settings, value="ON"):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_with_timestamp(Colors.YELLOW, f"💡 [DL1] {value} (Door LED 1)", time.strftime('%H:%M:%S', t))

    payload = {
        "measurement": "Door LED 1",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    # 1. Non-blocking /live publish (za reakciju servera)
    live_queue.put(('Door LED 1/live', json.dumps(payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        led_batch.append(('Door LED 1/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_led_lights(settings, threads, stop_event):
    if settings['simulated']:
        print_yellow("[DL1] Starting LED light simulator")
        door_led_light_thread = threading.Thread(target=run_door_led_light_simulator, args=(door_led_light_callback, settings, stop_event))
        door_led_light_thread.start()
        threads.append(door_led_light_thread)
        print_yellow("[DL1] LED light simulator started")
    else:
        from sensors.door_led_light import run_door_led_light_loop
        print_yellow("[DL1] Starting LED light loop")
        door_led_light_thread = threading.Thread(target=run_door_led_light_loop, args=(settings, door_led_light_callback, stop_event))
        door_led_light_thread.start()
        threads.append(door_led_light_thread)
        print_yellow("[DL1] LED light loop started")
