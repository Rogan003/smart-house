from colors import Colors, print_green, print_separator
from simulators.kitchen_dht import run_dht_simulator
import threading
import time
import json
import queue
import paho.mqtt.publish as publish
from broker_settings import HOSTNAME, PORT


dht_batch = []
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
            print(f"[DHT3] Live publish error: {e}")

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
        print(f'[DHT3] Published {publish_data_limit} kitchen DHT values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dht_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def dht_callback(humidity, temperature, publish_event, dht_settings, code="DHTLIB_OK", verbose=True):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        timestamp = time.strftime('%H:%M:%S', t)
        print()
        print(f"{Colors.GREEN}🌡️ [DHT3] {temperature}°C  💧 {humidity}%{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
        print_separator()

    temp_payload = {
        "measurement": "Temperature Kitchen",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": temperature
    }

    humidity_payload = {
        "measurement": "Humidity Kitchen",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": humidity
    }

    # 1. Non-blocking /live publish (za reakciju servera)
    live_queue.put(('Temperature Kitchen/live', json.dumps(temp_payload)))
    live_queue.put(('Humidity Kitchen/live', json.dumps(humidity_payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        dht_batch.append(('Humidity Kitchen/batch', json.dumps(humidity_payload), 0, True))
        dht_batch.append(('Temperature Kitchen/batch', json.dumps(temp_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_kitchen_dht(settings, threads, stop_event):
    if settings['simulated']:
        print_green("[DHT3] Starting simulator (Kitchen DHT)")
        kitchen_dht_thread = threading.Thread(target = run_dht_simulator, args=(2, dht_callback, stop_event, publish_event, settings))
        kitchen_dht_thread.start()
        threads.append(kitchen_dht_thread)
        print_green("[DHT3] Simulator started (Kitchen DHT)")
    else:
        from sensors.kitchen_dht import run_dht_loop, DHT
        print_green("[DHT3] Starting loop (Kitchen DHT)")
        dht = DHT(settings['pin'])
        kitchen_dht_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht_callback, stop_event, publish_event, settings))
        kitchen_dht_thread.start()
        threads.append(kitchen_dht_thread)
        print_green("[DHT3] Loop started (Kitchen DHT)")
