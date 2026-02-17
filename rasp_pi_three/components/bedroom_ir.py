from colors import print_white
import threading
import time
import json
import paho.mqtt.publish as publish

from simulators.bedroom_ir import run_bedroom_ir_simulator
from broker_settings import HOSTNAME, PORT
from rgb_controller import rgb_controller

ir_batch = []
publish_data_counter = 0
publish_data_limit = 5
counter_lock = threading.Lock()

def publisher_task(event, ir_batch):
    global publish_data_counter
    while True:
        event.wait()
        with counter_lock:
            local_ir_batch = ir_batch.copy()
            publish_data_counter = 0
            ir_batch.clear()
        publish.multiple(local_ir_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {len(local_ir_batch)} IR values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, ir_batch,))
publisher_thread.daemon = True
publisher_thread.start()

def bedroom_ir_callback(button, settings):
    global publish_data_counter, publish_data_limit

    t = time.localtime()
    print_white("\n" + "="*20)
    print_white(f"Bedroom IR: Button {button} pressed")
    print_white(f"Timestamp: {time.strftime('%H:%M:%S', t)}")

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
        rgb_controller.set_color("lightBlue")
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

    with counter_lock:
        ir_batch.append(('Bedroom IR', json.dumps(payload), 0, True))
        publish_data_counter += 1

    if publish_data_counter >= publish_data_limit:
        publish_event.set()

def run_bedroom_ir(settings, threads, stop_event, button=None):
    if settings['simulated']:
        if button is not None:
            print_white("[Bedroom IR] Starting simulator")
            thread = threading.Thread(target=run_bedroom_ir_simulator, args=(bedroom_ir_callback, settings, button))
            thread.start()
            threads.append(thread)
            print_white("[Bedroom IR] Simulator started")
    else:
        from sensors.bedroom_ir import run_bedroom_ir_loop
        print_white("[Bedroom IR] Starting loop")
        thread = threading.Thread(target=run_bedroom_ir_loop, args=(settings, bedroom_ir_callback, stop_event))
        thread.start()
        threads.append(thread)
        print_white("[Bedroom IR] Loop started")
