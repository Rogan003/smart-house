import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt

from colors import print_yellow

from broker_settings import HOSTNAME, PORT


led_state = False
led_pin = None


def turn_diode_on(pin):
    global led_state
    led_state = True
    print_yellow("[DL1] Door Light ON (Door LED 1)")
    GPIO.output(pin, GPIO.HIGH)


def turn_diode_off(pin):
    global led_state
    led_state = False
    print_yellow("[DL1] Door Light OFF (Door LED 1)")
    GPIO.output(pin, GPIO.LOW)


def on_connect(client, userdata, flags, rc):
    print_yellow("[DL1] Connected to MQTT broker, subscribing to LED Control")
    client.subscribe("LED Control")


def on_message(client, userdata, msg):
    global led_state, led_pin
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("command", "")
        target = payload.get("target", "")
        
        if target == "DL1" and led_pin is not None:
            if command == "ON" and not led_state:
                turn_diode_on(led_pin)
                # publish state change
                if userdata and 'callback' in userdata:
                    userdata['callback'](userdata['settings'], "ON")
            elif command == "OFF" and led_state:
                turn_diode_off(led_pin)
                # publish state change
                if userdata and 'callback' in userdata:
                    userdata['callback'](userdata['settings'], "OFF")
    except Exception as e:
        print_yellow(f"[DL1] Error processing message: {e}")


def run_door_led_light_loop(settings, callback, stop_event):
    global led_pin
    
    pin = settings['pin']
    led_pin = pin
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # start with LED off
    
    client = mqtt.Client(userdata={'callback': callback, 'settings': settings})
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(HOSTNAME, PORT, 60)
    client.loop_start()
    
    print_yellow("[DL1] Door LED started, waiting for commands...")
    
    # keep running until stop_event is set
    while not stop_event.is_set():
        time.sleep(0.5)
    
    client.loop_stop()
    client.disconnect()
    GPIO.output(pin, GPIO.LOW)
    print_yellow("[DL1] Door LED stopped")
