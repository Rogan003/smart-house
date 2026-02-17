from colors import print_blue
import threading
import time
import json
import paho.mqtt.publish as publish
from broker_settings import HOSTNAME, PORT
from simulators.master_bedroom_dht import run_dht_simulator

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
        print(f'published {publish_data_limit} master_bedroom dht values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, dht_batch,))
publisher_thread.daemon = True
publisher_thread.start()


def dht_callback(humidity, temperature, publish_event, dht_settings, code="DHTLIB_OK", verbose=True):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        print_blue("="*20)
        print_blue("Master Bedroom DHT")
        print_blue(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print_blue(f"Code: {code}")
        print_blue(f"Humidity: {humidity}%")
        print_blue(f"Temperature: {temperature}°C")

    temp_payload = {
        "measurement": "Temperature Master Bedroom",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": temperature
    }

    humidity_payload = {
        "measurement": "Humidity Master Bedroom",
        "simulated": dht_settings['simulated'],
        "runs_on": dht_settings["runs_on"],
        "name": dht_settings["name"],
        "value": humidity
    }

    with counter_lock:
        dht_batch.append(('Temperature Master Bedroom', json.dumps(temp_payload), 0, True))
        dht_batch.append(('Humidity Master Bedroom', json.dumps(humidity_payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()


def run_master_bedroom_dht(settings, threads, stop_event):
    if settings['simulated']:
        print_blue("[Master Bedroom DHT] Starting similator")
        master_bedroom_dht_thread = threading.Thread(target = run_dht_simulator, args=(2, dht_callback, stop_event, publish_event, settings))
        master_bedroom_dht_thread.start()
        threads.append(master_bedroom_dht_thread)
        print_blue("[Master Bedroom DHT] similator started")
    else:
        from sensors.master_bedroom_dht import run_dht_loop, DHT
        print_blue("[Master Bedroom DHT] Starting loop")
        dht = DHT(settings['pin'])
        master_bedroom_dht_thread = threading.Thread(target=run_dht_loop, args=(dht, 2, dht_callback, stop_event, publish_event, settings))
        master_bedroom_dht_thread.start()
        threads.append(master_bedroom_dht_thread)
        print_blue("[Master Bedroom DHT] loop started")
