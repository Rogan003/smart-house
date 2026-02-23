from colors import Colors, print_magenta, print_separator
import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.bedroom_rgb import run_bedroom_rgb_simulator
from broker_settings import HOSTNAME, PORT

rgb_batch = []
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
            print(f"[BRGB] error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, rgb_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_rgb_batch = rgb_batch.copy()
            publish_data_counter = 0
            rgb_batch.clear()
        publish.multiple(local_rgb_batch, hostname=HOSTNAME, port=PORT)
        print(f'[BRGB] Published {len(local_rgb_batch)} RGB values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, rgb_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def get_color_for_value(color_str):
    # map color string to Colors constant
    if color_str == "off":
        return Colors.GRAY
    elif "255,0,0" in color_str or color_str == "red":
        return Colors.RED
    elif "0,255,0" in color_str or color_str == "green":
        return Colors.GREEN
    elif "0,0,255" in color_str or color_str == "blue":
        return Colors.BLUE
    elif "255,255,0" in color_str or color_str == "yellow":
        return Colors.YELLOW
    elif "255,0,255" in color_str or color_str == "purple":
        return Colors.MAGENTA
    elif "0,255,255" in color_str or color_str == "cyan":
        return Colors.CYAN
    elif "255,255,255" in color_str or color_str == "white":
        return Colors.WHITE
    else:
        return Colors.WHITE

def bedroom_rgb_callback(color, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    print()
    
    color_code = get_color_for_value(color)
    print(f"{Colors.MAGENTA}🌈 [BRGB]{Colors.RESET} {color_code}{color}{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    payload = {
        "measurement": "Bedroom RGB",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": color
    }

    # send to live topic
    live_queue.put(('Bedroom RGB/live', json.dumps(payload)))

    # add to batch
    with counter_lock:
        rgb_batch.append(('Bedroom RGB/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_bedroom_rgb(settings, threads, stop_event):
    if settings['simulated']:
        print_magenta("[BRGB] Starting simulator (Bedroom RGB)")
        thread = threading.Thread(target=run_bedroom_rgb_simulator, args=(bedroom_rgb_callback, stop_event, settings))
        thread.start()
        threads.append(thread)
        print_magenta("[BRGB] Simulator started (Bedroom RGB)")
    else:
        from sensors.bedroom_rgb import run_bedroom_rgb_loop
        print_magenta("[BRGB] Starting loop (Bedroom RGB)")
        thread = threading.Thread(target=run_bedroom_rgb_loop, args=(settings, bedroom_rgb_callback, stop_event))
        thread.start()
        threads.append(thread)
        print_magenta("[BRGB] Loop started (Bedroom RGB)")
