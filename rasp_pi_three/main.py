import threading
import json
import paho.mqtt.client as mqtt

from components.living_room_motion_sensor import run_living_room_motion_sensor
from components.bedroom_dht import run_bedroom_dht
from components.master_bedroom_dht import run_master_bedroom_dht
from components.living_room_display import run_living_room_display
from components.bedroom_rgb import run_bedroom_rgb
from components.bedroom_ir import run_bedroom_ir

from settings import load_settings
from broker_settings import HOSTNAME, PORT
from rgb_controller import rgb_controller
from dht_storage import dht_storage
import time


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("RGB Control")
    client.subscribe("Temperature Kitchen")
    client.subscribe("Humidity Kitchen")
    print("[MQTT] Subscribed to RGB Control, Temperature Kitchen and Humidity Kitchen topics")


def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        print(f"[MQTT] Received on {topic}: {payload}")

        if topic == "RGB Control":
            command = payload.get("command")
            if command == "ON":
                color = payload.get("color", {"r": 255, "g": 255, "b": 255})
                rgb_controller.set_color(f"rgb({color['r']},{color['g']},{color['b']})")
                print(f"[RGB] Turned ON with color: {color}")
            elif command == "OFF":
                rgb_controller.set_color("off")
                print("[RGB] Turned OFF")
            elif command == "COLOR":
                color = payload.get("color", {"r": 255, "g": 0, "b": 0})
                rgb_controller.set_color(f"rgb({color['r']},{color['g']},{color['b']})")
                print(f"[RGB] Color set to: {color}")

        elif topic == "Temperature Kitchen":
            temp = payload.get("value")
            _, hum = dht_storage.get_dht3()
            dht_storage.update_dht3(temp, hum)
            print(f"[DHT3] Temperature Kitchen updated: {temp}")

        elif topic == "Humidity Kitchen":
            hum = payload.get("value")
            temp, _ = dht_storage.get_dht3()
            dht_storage.update_dht3(temp, hum)
            print(f"[DHT3] Humidity Kitchen updated: {hum}")

    except Exception as e:
        print(f"[MQTT] Error processing message: {e}")

def menu(settings, threads, stop_event):
    bedroom_ir_settings = settings['bedroom_infrared']
    while True:
        print("\n---- Menu ----")
        if bedroom_ir_settings['simulated']:
            print("1. Bedroom IR")
        print()

        user_input = input("Enter command: ")

        if user_input == "1" and bedroom_ir_settings['simulated']:
            button = input("Enter button (0-7): ")
            run_bedroom_ir(bedroom_ir_settings, threads, stop_event, button)
        else:
            print("Oops, invalid command!")


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(HOSTNAME, PORT, 60)
    mqtt_client.loop_start()
    print("[MQTT] Subscriber client started")

    try:
        bedroom_dht_settings = settings['bedroom_dht']
        run_bedroom_dht(bedroom_dht_settings, threads, stop_event)

        master_bedroom_dht_settings = settings['master_bedroom_dht']
        run_master_bedroom_dht(master_bedroom_dht_settings, threads, stop_event)

        living_room_motion_sensor_settings = settings['living_room_motion_sensor']
        run_living_room_motion_sensor(living_room_motion_sensor_settings, threads, stop_event)

        living_room_display_settings = settings['living_room_display']
        run_living_room_display(living_room_display_settings, threads, stop_event)

        bedroom_rgb_settings = settings['bedroom_rgb']
        run_bedroom_rgb(bedroom_rgb_settings, threads, stop_event)

        bedroom_ir_settings = settings['bedroom_infrared']
        if not bedroom_ir_settings['simulated']:
            run_bedroom_ir(bedroom_ir_settings, threads, stop_event)

        menu(settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        for t in threads:
            stop_event.set()