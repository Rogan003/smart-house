from colors import Colors, print_gray, print_white, print_separator

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.door_button_two import run_door_button_two_simulator
from broker_settings import HOSTNAME, PORT


button_batch = []
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
            print(f"[DS2] error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, button_batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_button_batch = button_batch.copy()
            publish_data_counter = 0
            button_batch.clear()
        publish.multiple(local_button_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} button values')
        event.clear()


publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, button_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def door_button_two_callback(settings, value="TRUE"):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    status = "OPEN" if value == "TRUE" else "CLOSED"
    emoji = "🚪" if value == "TRUE" else "🔒"
    color = Colors.CYAN if value == "TRUE" else Colors.GREEN
    print()
    print(f"{color}{emoji} [DS2] {status}{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    payload = {
        "measurement": "Door button 2",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    # send to live topic
    live_queue.put(('Door Button 2/live', json.dumps(payload)))

    # add to batch
    with counter_lock:
        button_batch.append(('Door Button 2/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_door_button_two(settings, threads, stop_event):
    if settings['simulated']:
        print_white("[Door 2] Starting button simulator")
        door_button_two_thread = threading.Thread(target = run_door_button_two_simulator, args=(2, settings, door_button_two_callback, stop_event))
        door_button_two_thread.start()
        threads.append(door_button_two_thread)
        print_white("[Door 2] Button simulator started")
    else:
        from sensors.door_button_two import run_door_button_two_loop
        print_white("[Door 2] Starting button loop")
        door_button_two_thread = threading.Thread(target=run_door_button_two_loop, args=(settings, door_button_two_callback, stop_event))
        door_button_two_thread.start()
        threads.append(door_button_two_thread)
        print_white("[Door 2] Button loop started")
