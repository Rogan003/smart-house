import threading
import json
import paho.mqtt.client as mqtt

from components.door_button_two import run_door_button_two
from components.door_motion_sensor_two import run_door_motion_sensor_two
from components.door_ultrasonic_sensor_two import run_door_ultrasonic_sensor_two
from components.kitchen_button import run_kitchen_button, run_kitchen_button_continuous
from components.kitchen_dht import run_kitchen_dht
from components.kitchen_segment_display import run_kitchen_segment_display
from components.gyroscope import run_gyroscope

from settings import load_settings
from broker_settings import HOSTNAME, PORT
from kitchen_timer import kitchen_timer
import time


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("Timer Display")
    client.subscribe("Timer Control")
    print("[MQTT] Subscribed to Timer Display and Timer Control topics")


def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if topic == "Timer Display":
            command = payload.get("command")
            if command == "SET":
                value = payload.get("value", "00:00")
                # Parse MM:SS format
                parts = value.split(":")
                if len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    total_seconds = minutes * 60 + seconds
                    kitchen_timer.set_time(total_seconds)
                    # Only print for last 5 seconds (silent otherwise)
                    # Printing is handled by the 4SD simulator
            elif command == "BLINK":
                kitchen_timer.set_blinking(True)
                # Rainbow print is handled by 4SD simulator
            elif command == "STOP_BLINK":
                kitchen_timer.set_blinking(False)
                print("[Timer] Blinking stopped")

        elif topic == "Timer Control":
            command = payload.get("command")
            if command == "CONFIGURE":
                add_seconds = payload.get("add_seconds", 10)
                kitchen_timer.n = add_seconds
                print(f"[Timer] Configured BTN to add {add_seconds} seconds")

    except Exception as e:
        print(f"[MQTT] Error processing message: {e}")

def menu(settings, threads, stop_event):
    kitchen_button_settings = settings['kitchen_button']

    while True:
        print("\n---- Menu ----")
        if kitchen_button_settings['simulated']:
            print("1. click kitchen button")
        print()

        user_input = input("Enter command: ")

        if user_input == "1" and kitchen_button_settings['simulated']:
            run_kitchen_button(kitchen_button_settings, threads, stop_event)

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
        door_button_two_settings = settings['door_button_two']
        run_door_button_two(door_button_two_settings, threads, stop_event)

        door_motion_sensor_two_settings = settings['door_motion_sensor_two']
        run_door_motion_sensor_two(door_motion_sensor_two_settings, threads, stop_event)

        door_ultrasonic_sensor_two_settings = settings['door_ultrasonic_sensor_two']
        run_door_ultrasonic_sensor_two(door_ultrasonic_sensor_two_settings, threads, stop_event)

        kitchen_dht_settings = settings['kitchen_dht']
        run_kitchen_dht(kitchen_dht_settings, threads, stop_event)

        kitchen_segment_display_settings = settings['kitchen_segment_display']
        run_kitchen_segment_display(kitchen_segment_display_settings, threads, stop_event)

        gyroscope_settings = settings['kitchen_gyroscope']
        run_gyroscope(gyroscope_settings, threads, stop_event)

        kitchen_button_settings = settings['kitchen_button']
        run_kitchen_button_continuous(kitchen_button_settings, threads, stop_event)

        menu(settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        for t in threads:
            stop_event.set()