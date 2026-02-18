import threading
import json
import paho.mqtt.client as mqtt

from components.door_led_light import run_door_led_lights
from components.door_buzzer_one import run_door_buzzer_one, run_door_buzzer_one_continuous
from components.door_membrane_switch import run_door_membrane_switch

from components.door_button_one import run_door_button_one
from components.door_motion_sensor_one import run_door_motion_sensor_one
from components.door_ultrasonic_sensor_one import run_door_ultrasonic_sensor_one

from settings import load_settings
from broker_settings import HOSTNAME, PORT
from buzzer_controller import buzzer_controller
import time


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


# MQTT subscriber for control messages
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("Buzzer Control")
    print("[MQTT] Subscribed to Buzzer Control topic")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        print(f"[MQTT] Received on {topic}: {payload}")

        if topic == "Buzzer Control":
            command = payload.get("command")
            if command == "ON":
                buzzer_controller.turn_on()
                print("\n🚨 [DB1] ALARM ACTIVATED! Buzzer ON (Door Buzzer 1)")
                print("------------------------------------------------------------")
            elif command == "OFF":
                buzzer_controller.turn_off()
                print("\n🔕 [DB1] ALARM DEACTIVATED! Buzzer OFF (Door Buzzer 1)")
                print("------------------------------------------------------------")

    except Exception as e:
        print(f"[MQTT] Error processing message: {e}")

def menu(settings, threads, stop_event):
    door_led_light_settings = settings['door_led_light']
    door_buzzer_one_settings = settings['door_buzzer']
    door_membrane_switch_settings = settings['door_membrane_switch']

    while True:
        print("\n---- Menu ----")
        print("1. toggle door light")
        print("2. buzz")
        print("3. keypad press\n")

        user_input = input("Enter command: ")

        if user_input == "1":
            run_door_led_lights(door_led_light_settings, threads, stop_event)

        elif user_input == "2":
            run_door_buzzer_one(door_buzzer_one_settings, threads, stop_event)

        elif user_input == "3":
            try:
                row = int(input("Enter Row (1-4): ")) - 1
                col = int(input("Enter Column (1-4): ")) - 1
                if 0 <= row <= 3 and 0 <= col <= 3:
                    run_door_membrane_switch(door_membrane_switch_settings, threads, stop_event, row, col)
                else:
                    print("Invalid input. Please use 1-4.")
            except ValueError:
                print("Invalid input. Please enter numbers.")

        else:
            print("Oops, invalid command!\n")
        print()


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    # start MQTT subscriber client for control messages
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(HOSTNAME, PORT, 60)
    mqtt_client.loop_start()
    print("[MQTT] Subscriber client started")

    try:
        door_button_one_settings = settings['door_button_one']
        run_door_button_one(door_button_one_settings, threads, stop_event)

        door_motion_sensor_one_settings = settings['door_motion_sensor_one']
        run_door_motion_sensor_one(door_motion_sensor_one_settings, threads, stop_event)

        door_ultrasonic_sensor_one_settings = settings['door_ultrasonic_sensor_one']
        run_door_ultrasonic_sensor_one(door_ultrasonic_sensor_one_settings, threads, stop_event)

        # start DL1 LED light (listens for MQTT commands from server)
        door_led_light_settings = settings['door_led_light']
        run_door_led_lights(door_led_light_settings, threads, stop_event)

        # start continuous buzzer that listens for MQTT control messages (alarm)
        door_buzzer_one_settings = settings['door_buzzer']
        run_door_buzzer_one_continuous(door_buzzer_one_settings, threads, stop_event)

        menu(settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        for t in threads:
            stop_event.set()