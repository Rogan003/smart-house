from colors import print_green
from simulators.kitchen_dht import run_dht_simulator
import threading
import time
import json
import paho.mqtt.publish as publish
from broker_settings import HOSTNAME, PORT


dht_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()


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
        print_green("="*20)
        print_green("[DHT3] Kitchen DHT")
        print_green(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print_green(f"Code: {code}")
        print_green(f"Humidity: {humidity}%")
        print_green(f"Temperature: {temperature}°C")

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

    with counter_lock:
        dht_batch.append(('Temperature Kitchen', json.dumps(temp_payload), 0, True))
        dht_batch.append(('Humidity Kitchen', json.dumps(humidity_payload), 0, True))
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
