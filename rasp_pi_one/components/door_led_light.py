from colors import print_white, print_yellow, Colors, print_with_timestamp

import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.door_led_light import run_door_led_light_simulator
from broker_settings import HOSTNAME, PORT


led_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()


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
    print_with_timestamp(Colors.YELLOW, f"[DL1] {value} (Door LED 1)", time.strftime('%H:%M:%S', t))

    led_payload = {
        "measurement": "Door LED 1",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    with counter_lock:
        led_batch.append(('Door LED 1', json.dumps(led_payload), 0, True))
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
