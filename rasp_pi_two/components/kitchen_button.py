from colors import Colors, print_gray, print_red, print_separator

import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from broker_settings import HOSTNAME, PORT
from simulators.kitchen_button import run_kitchen_button_simulator
from kitchen_timer import kitchen_timer

button_batch = []
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
            print(f"[BTN] Live publish error: {e}")

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

def kitchen_button_callback(settings):
    global publish_data_counter, publish_data_limit
    if kitchen_timer.is_blinking():
        kitchen_timer.set_blinking(False)
    else:
        kitchen_timer.increment()

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    print()
    print(f"{Colors.YELLOW}🔘 [BTN] Kitchen Button pressed{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    payload = {
        "measurement": "Kitchen Button",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": "TRUE"
    }

    # 1. Non-blocking /live publish (za reakciju servera)
    live_queue.put(('Kitchen Button/live', json.dumps(payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        button_batch.append(('Kitchen Button/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_kitchen_button(settings, threads, stop_event):
    if settings['simulated']:
        print_red("[Kitchen Button] Starting button simulator")
        kitchen_button_thread = threading.Thread(target = run_kitchen_button_simulator, args=(settings, kitchen_button_callback))
        kitchen_button_thread.start()
        threads.append(kitchen_button_thread)
    else:
        from sensors.kitchen_button import run_kitchen_button_loop
        print_red("[Kitchen Button] Starting button loop")
        kitchen_button_thread = threading.Thread(target=run_kitchen_button_loop, args=(settings, kitchen_button_callback, stop_event))
        kitchen_button_thread.start()
        threads.append(kitchen_button_thread)
