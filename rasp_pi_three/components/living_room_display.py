from colors import Colors, print_blue, print_separator
import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.living_room_display import run_living_room_display_simulator
from broker_settings import HOSTNAME, PORT

lcd_batch = []
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
            print(f"[LCD] error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, lcd_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_lcd_batch = lcd_batch.copy()
            publish_data_counter = 0
            lcd_batch.clear()
        publish.multiple(local_lcd_batch, hostname=HOSTNAME, port=PORT)
        print(f'[LCD] Published {len(local_lcd_batch)} LCD values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, lcd_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def living_room_display_callback(line1, line2, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    print()
    print(f"{Colors.BLUE}📺 [LCD] {line1} | {line2}{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    payload = {
        "measurement": "Living Room Display",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": f"{line1} | {line2}"
    }

    # send to live topic
    live_queue.put(('Living Room Display/live', json.dumps(payload)))

    # add to batch
    with counter_lock:
        lcd_batch.append(('Living Room Display/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_living_room_display(settings, threads, stop_event):
    if settings['simulated']:
        print_blue("[LCD] Starting simulator (Living Room Display)")
        thread = threading.Thread(target=run_living_room_display_simulator, args=(living_room_display_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_blue("[LCD] Simulator started (Living Room Display)")
    else:
        from sensors.living_room_display import run_living_room_display_loop
        print_blue("[LCD] Starting loop (Living Room Display)")
        thread = threading.Thread(target=run_living_room_display_loop, args=(settings, living_room_display_callback, stop_event))
        thread.start()
        threads.append(thread)
        print_blue("[LCD] Loop started (Living Room Display)")
