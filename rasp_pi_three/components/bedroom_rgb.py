from colors import print_magenta
import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.bedroom_rgb import run_bedroom_rgb_simulator
from broker_settings import HOSTNAME, PORT

rgb_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, rgb_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_rgb_batch = rgb_batch.copy()
            publish_data_counter = 0
            rgb_batch.clear()
        publish.multiple(local_rgb_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {len(local_rgb_batch)} RGB values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, rgb_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def bedroom_rgb_callback(color, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_magenta("\n" + "="*20)
    print_magenta(f"Bedroom RGB: {color}")
    print_magenta(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

    payload = {
        "measurement": "Bedroom RGB",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": color
    }

    with counter_lock:
        rgb_batch.append(('Bedroom RGB', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_bedroom_rgb(settings, threads, stop_event):
    if settings['simulated']:
        print_magenta("[Bedroom RGB] Starting simulator")
        thread = threading.Thread(target=run_bedroom_rgb_simulator, args=(bedroom_rgb_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_magenta("[Bedroom RGB] Simulator started")
    else:
        from sensors.bedroom_rgb import run_bedroom_rgb_loop
        print_magenta("[Bedroom RGB] Starting loop")
        thread = threading.Thread(target=run_bedroom_rgb_loop, args=(settings, bedroom_rgb_callback, stop_event))
        thread.start()
        threads.append(thread)
        print_magenta("[Bedroom RGB] Loop started")
