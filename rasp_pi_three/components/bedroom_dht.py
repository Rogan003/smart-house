from colors import Colors, print_green, print_separator
import threading
import time
import json
import queue
import paho.mqtt.publish as publish
from broker_settings import HOSTNAME, PORT
from simulators.bedroom_dht import run_dht_simulator
from dht_storage import dht_storage

dht_batch = []
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
            print(f"[DHT1] error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, dht_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_dht_batch = dht_batch.copy()
            publish_data_counter = 0
            dht_batch.clear()
        publish.multiple(local_dht_batch, hostname=HOSTNAME, port=PORT)
        print(f'[DHT1] Published {publish_data_limit} bedroom DHT values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dht_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def dht_callback(humidity, temperature, publish_event, dht_settings, code="DHTLIB_OK", verbose=True):
    global publish_data_counter, publish_data_limit
    dht_storage.update_dht1(temperature, humidity)

    if verbose:
        t = time.localtime()
        timestamp = time.strftime('%H:%M:%S', t)
        print()
        print(f"{Colors.GREEN}🌡️ [DHT1] {temperature}°C  💧 {humidity}%{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
        print_separator()

    temp_payload = {
        "measurement": "Temperature Bedroom",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": temperature
    }

    humidity_payload = {
        "measurement": "Humidity Bedroom",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": humidity
    }

    # send to live topic
    live_queue.put(('Temperature Bedroom/live', json.dumps(temp_payload)))
    live_queue.put(('Humidity Bedroom/live', json.dumps(humidity_payload)))

    # add to batch
    with counter_lock:
        dht_batch.append(('Humidity Bedroom/batch', json.dumps(humidity_payload), 0, True))
        dht_batch.append(('Temperature Bedroom/batch', json.dumps(temp_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_bedroom_dht(settings, threads, stop_event):
    if settings['simulated']:
        print_green("[DHT1] Starting simulator (Bedroom DHT)")
        bedroom_dht_thread = threading.Thread(target = run_dht_simulator, args=(4, dht_callback, stop_event, publish_event, settings))
        bedroom_dht_thread.start()
        threads.append(bedroom_dht_thread)
        print_green("[DHT1] Simulator started (Bedroom DHT)")
    else:
        from sensors.bedroom_dht import run_dht_loop, DHT
        print_green("[DHT1] Starting loop (Bedroom DHT)")
        dht = DHT(settings['pin'])
        bedroom_dht_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht_callback, stop_event, publish_event, settings))
        bedroom_dht_thread.start()
        threads.append(bedroom_dht_thread)
        print_green("[DHT1] Loop started (Bedroom DHT)")
