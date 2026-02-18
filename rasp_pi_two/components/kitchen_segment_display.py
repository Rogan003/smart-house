from colors import print_blue
import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.kitchen_segment_display import run_kitchen_segment_display_simulator
from broker_settings import HOSTNAME, PORT

segment_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

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

def kitchen_segment_display_callback(settings, timer_val):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_blue("\n" + "="*20)
    print_blue(f"[4SD] Display: {timer_val} (Kitchen Segment Display)")
    print_blue(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

    payload = {
        "measurement": "Kitchen Segment Display",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": timer_val
    }

    with counter_lock:
        segment_batch.append(('Kitchen Segment Display', json.dumps(payload), 0, True))
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
