from colors import Colors, print_yellow, print_separator

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.gyroscope import run_gyroscope_simulator
from broker_settings import HOSTNAME, PORT

gyro_batch = []
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
            print(f"[GSG] Live publish error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, gyro_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_gyro_batch = gyro_batch.copy()
            publish_data_counter = 0
            gyro_batch.clear()
        publish.multiple(local_gyro_batch, hostname=HOSTNAME, port=PORT)
        print(f'[GSG] Published {len(local_gyro_batch)} gyro values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, gyro_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def gyroscope_callback(accel, gyro, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    accel_str = [f"{v:.1f}" for v in accel]
    gyro_str = [f"{v:.1f}" for v in gyro]
    print()
    print(f"{Colors.YELLOW}🎯 [GSG] Accel: {accel_str}  🔄 Gyro: {gyro_str}{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    axes = ['X', 'Y', 'Z']
    
    # 1. Non-blocking /live publish (za reakciju servera)
    for i, axis in enumerate(axes):
        accel_payload = {
            "measurement": f"Accelerometer {axis}",
            "simulated": settings['simulated'],
            "runs_on": settings["runs_on"],
            "name": settings["name"],
            "value": accel[i]
        }
        live_queue.put((f'Accelerometer {axis}/live', json.dumps(accel_payload)))

    for i, axis in enumerate(axes):
        gyro_payload = {
            "measurement": f"Gyroscope {axis}",
            "simulated": settings['simulated'],
            "runs_on": settings["runs_on"],
            "name": settings["name"],
            "value": gyro[i]
        }
        live_queue.put((f'Gyroscope {axis}/live', json.dumps(gyro_payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        for i, axis in enumerate(axes):
            accel_payload = {
                "measurement": f"Accelerometer {axis}",
                "simulated": settings['simulated'],
                "runs_on": settings["runs_on"],
                "name": settings["name"],
                "value": accel[i]
            }
            gyro_batch.append((f'Accelerometer {axis}/batch', json.dumps(accel_payload), 0, True))

        for i, axis in enumerate(axes):
            gyro_payload = {
                "measurement": f"Gyroscope {axis}",
                "simulated": settings['simulated'],
                "runs_on": settings["runs_on"],
                "name": settings["name"],
                "value": gyro[i]
            }
            gyro_batch.append((f'Gyroscope {axis}/batch', json.dumps(gyro_payload), 0, True))
            
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_gyroscope(settings, threads, stop_event):
    if settings['simulated']:
        print_yellow("[GSG] Starting simulator (Gyroscope Sensor)")
        thread = threading.Thread(target=run_gyroscope_simulator, args=(2, gyroscope_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_yellow("[GSG] Simulator started (Gyroscope Sensor)")
    else:
        from sensors.MPU6050.gyro import run_gyroscope_loop
        print_yellow("[GSG] Starting loop (Gyroscope Sensor)")
        thread = threading.Thread(target=run_gyroscope_loop, args=(2, gyroscope_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_yellow("[GSG] Loop started (Gyroscope Sensor)")
