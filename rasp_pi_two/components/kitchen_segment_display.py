from colors import Colors, print_blue, print_separator, print_gray
import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.kitchen_segment_display import run_kitchen_segment_display_simulator
from broker_settings import HOSTNAME, PORT

segment_batch = []
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
            print(f"[4SD] Live publish error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, segment_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_segment_batch = segment_batch.copy()
            publish_data_counter = 0
            segment_batch.clear()
        publish.multiple(local_segment_batch, hostname=HOSTNAME, port=PORT)
        print(f'[4SD] Published {len(local_segment_batch)} segment display values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, segment_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def kitchen_segment_display_callback(settings, timer_val, verbose=True):
    global publish_data_counter, publish_data_limit

    if verbose:
        t = time.localtime()
        timestamp = time.strftime('%H:%M:%S', t)
        print()
        print(f"{Colors.BLUE}🔢 [4SD] {timer_val}{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
        print_separator()

    payload = {
        "measurement": "Kitchen Segment Display",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": timer_val
    }

    # 1. Non-blocking /live publish (za reakciju servera)
    live_queue.put(('Kitchen Segment Display/live', json.dumps(payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        segment_batch.append(('Kitchen Segment Display/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_kitchen_segment_display(settings, threads, stop_event):
    if settings['simulated']:
        print_blue("[4SD] Starting simulator (Kitchen Segment Display)")
        thread = threading.Thread(target=run_kitchen_segment_display_simulator, args=(kitchen_segment_display_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_blue("[4SD] Simulator started (Kitchen Segment Display)")
    else:
        from sensors.kitchen_segment_display import run_kitchen_segment_display_loop
        print_blue("[4SD] Starting loop (Kitchen Segment Display)")
        thread = threading.Thread(target=run_kitchen_segment_display_loop, args=(settings, kitchen_segment_display_callback, stop_event))
        thread.start()
        threads.append(thread)
        print_blue("[4SD] Loop started (Kitchen Segment Display)")
