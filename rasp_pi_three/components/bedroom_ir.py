from colors import Colors, print_white, print_separator
import threading
import time
import json
import queue
import paho.mqtt.publish as publish

from simulators.bedroom_ir import run_bedroom_ir_simulator
from broker_settings import HOSTNAME, PORT
from rgb_controller import rgb_controller

ir_batch = []
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
            print(f"[IR] Live publish error: {e}")

live_publisher_thread = threading.Thread(target=live_publisher_task, daemon=True)
live_publisher_thread.start()


def publisher_task(event, ir_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_ir_batch = ir_batch.copy()
            publish_data_counter = 0
            ir_batch.clear()
        publish.multiple(local_ir_batch, hostname=HOSTNAME, port=PORT)
        print(f'[IR] Published {len(local_ir_batch)} IR values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ir_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def bedroom_ir_callback(button, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    print()
    print(f"{Colors.WHITE}📡 [IR] Button {button} pressed{Colors.RESET}  {Colors.GRAY}[{timestamp}]{Colors.RESET}")
    print_separator()

    # Control RGB
    if button == "1":
        rgb_controller.set_color("red")
    elif button == "2":
        rgb_controller.set_color("green")
    elif button == "3":
        rgb_controller.set_color("blue")
    elif button == "4":
        rgb_controller.set_color("yellow")
    elif button == "5":
        rgb_controller.set_color("purple")
    elif button == "6":
        rgb_controller.set_color("cyan")
    elif button == "7":
        rgb_controller.set_color("white")
    elif button == "0":
        rgb_controller.set_color("off")

    payload = {
        "measurement": "Bedroom IR",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": button
    }

    # 1. Non-blocking /live publish (za reakciju servera)
    live_queue.put(('Bedroom IR/live', json.dumps(payload)))

    # 2. Dodaj u batch (za InfluxDB) - šalje daemon nit
    with counter_lock:
        ir_batch.append(('Bedroom IR/batch', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_bedroom_ir(settings, threads, stop_event, button=None):
    if settings['simulated']:
        if button is not None:
            print_white("[IR] Starting simulator (Bedroom IR Receiver)")
            thread = threading.Thread(target=run_bedroom_ir_simulator, args=(bedroom_ir_callback, settings, button))
            thread.start()
            threads.append(thread)
            print_white("[IR] Simulator started (Bedroom IR Receiver)")
    else:
        from sensors.bedroom_ir import run_bedroom_ir_loop
        print_white("[IR] Starting loop (Bedroom IR Receiver)")
        thread = threading.Thread(target=run_bedroom_ir_loop, args=(settings, bedroom_ir_callback, stop_event))
        thread.start()
        threads.append(thread)
        print_white("[IR] Loop started (Bedroom IR Receiver)")
