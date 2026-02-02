from colors import print_gray, print_yellow

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
        print(f'published {publish_data_limit} led values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, led_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def door_led_light_callback(settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_gray("\n" + "="*20)
    print_gray(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

    led_payload = {
        "measurement": "LED",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": "active"
    }

    with counter_lock:
        led_batch.append(('LED', json.dumps(led_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_door_led_lights(settings, threads, stop_event):
    if settings['simulated']:
        print_yellow("[Door 1] Starting LED light simulator")
        door_led_light_thread = threading.Thread(target = run_door_led_light_simulator, args=(door_led_light_callback, settings))
        door_led_light_thread.start()
        threads.append(door_led_light_thread)
    else:
        from sensors.door_led_light import run_door_led_light_loop
        print_yellow("[Door 1] Starting LED light loop")
        door_led_light_thread = threading.Thread(target=run_door_led_light_loop, args=(settings, door_led_light_callback, stop_event))
        door_led_light_thread.start()
        threads.append(door_led_light_thread)
