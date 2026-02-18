import time
import json
import paho.mqtt.client as mqtt

from broker_settings import HOSTNAME, PORT


led_state = False


def turn_diode_on():
    global led_state
    led_state = True


def turn_diode_off():
    global led_state
    led_state = False


def on_connect(client, userdata, flags, rc):
    print("[DL1] Connected to MQTT broker, subscribing to LED Control")
    client.subscribe("LED Control")


def on_message(client, userdata, msg):
    global led_state
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("command", "")
        target = payload.get("target", "")
        
        if target == "DL1":
            if command == "ON" and not led_state:
                turn_diode_on()
                print("\n💡 [DL1] LED turned ON (Door Light 1)")
                print("------------------------------------------------------------")
                # publish state change
                if userdata and 'callback' in userdata:
                    userdata['callback'](userdata['settings'], "ON")
            elif command == "OFF" and led_state:
                turn_diode_off()
                print("\n💡 [DL1] LED turned OFF (Door Light 1)")
                print("------------------------------------------------------------")
                # publish state change
                if userdata and 'callback' in userdata:
                    userdata['callback'](userdata['settings'], "OFF")
    except Exception as e:
        print(f"[DL1] Error processing message: {e}")


def run_door_led_light_simulator(callback, settings, stop_event):
    client = mqtt.Client(userdata={'callback': callback, 'settings': settings})
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(HOSTNAME, PORT, 60)
    client.loop_start()
    
    print("[DL1] Door LED simulator started, waiting for commands...")
    
    # keep running until stop_event is set
    while not stop_event.is_set():
        time.sleep(0.5)
    
    client.loop_stop()
    client.disconnect()
    print("[DL1] Door LED simulator stopped")
