from colors import print_yellow
import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.gyroscope import run_gyroscope_simulator
from broker_settings import HOSTNAME, PORT

gyro_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, gyro_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_gyro_batch = gyro_batch.copy()
            publish_data_counter = 0
            gyro_batch.clear()
        publish.multiple(local_gyro_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {len(local_gyro_batch)} gyro values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, gyro_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def gyroscope_callback(accel, gyro, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_yellow("\n" + "="*20)
    print_yellow(f"Accelerometer: {accel}")
    print_yellow(f"Gyroscope: {gyro}")
    print_yellow(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

    payload = {
        "measurement": "Gyroscope",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": {
            "accel": accel,
            "gyro": gyro
        }
    }

    with counter_lock:
        gyro_batch.append(('Gyroscope', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_gyroscope(settings, threads, stop_event):
    if settings['simulated']:
        print_yellow("[Gyroscope] Starting gyroscope simulator")
        thread = threading.Thread(target=run_gyroscope_simulator, args=(2, gyroscope_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_yellow("[Gyroscope] Gyroscope simulator started")
    else:
        from sensors.MPU6050.gyro import run_gyroscope_loop
        print_yellow("[Gyroscope] Starting gyroscope loop")
        thread = threading.Thread(target=run_gyroscope_loop, args=(2, gyroscope_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_yellow("[Gyroscope] Gyroscope loop started")
