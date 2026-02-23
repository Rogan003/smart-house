from flask import Flask, jsonify, request
from flask_cors import CORS
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime
import logging

# terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_color(color, message):
    print(f"{color}{message}{Colors.ENDC}")

def print_gray(message):
    print_color(Colors.GRAY, message)

def print_green(message):
    print_color(Colors.GREEN, message)

def print_yellow(message):
    print_color(Colors.YELLOW, message)

def print_red(message):
    print_color(Colors.RED, message)

def print_cyan(message):
    print_color(Colors.CYAN, message)

def print_blue(message):
    print_color(Colors.BLUE, message)

# hide flask logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization", "X-Requested-With"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


# influxdb config
token = "MnETT6nOjyevCYF5obDzluansp1gyd1w9JbFSutVKUIXNtV6S8EaUeE-LBbMQ7pGUzTpJCJTP39jdks5TlyZoQ=="
org = "iot"
url = "http://localhost:8086"
bucket = "iot"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)


# global states
alarm_state = False
system_active = True
people_count = 1
empty_house_acknowledged = False  # alarm triggers on NEXT motion after house becomes empty
timer_seconds = 30
timer_add_seconds = 10
timer_blinking = False
timer_just_set = False  # skip first countdown after set
rgb_on = False
rgb_color = {"r": 255, "g": 0, "b": 0}
sensor_data = {}
state_lock = threading.Lock()

# PIN code
CORRECT_PIN = "11"
entered_pin = ""
system_activation_timer = None

# door open tracking for ALARM (DS1, DS2 open > 5 seconds)
door_open_time = {"DS1": None, "DS2": None}

# distance history for people counting (entry/exit detection)
distance_history = {"DUS1": [], "DUS2": []}
DISTANCE_HISTORY_LIMIT = 10  # keep last 10 readings
ENTRY_EXIT_THRESHOLD = 50  # cm - threshold to detect entry/exit

dl1_timer = None

# gyroscope
gyroscope_baseline = {"x": 0, "y": 0, "z": 0}
gyroscope_calibrated = False
GYROSCOPE_THRESHOLD = 30

# DHT values for LCD rotation
dht_values = {
    "DHT1": {"temp": 0, "humidity": 0},
    "DHT2": {"temp": 0, "humidity": 0},
    "DHT3": {"temp": 0, "humidity": 0}
}


# mqtt setup
mqtt_client = mqtt.Client()

# base topics (without /live or /batch suffix)
MQTT_BASE_TOPICS = [
    "Door Button 1",
    "Door Buzzer 1",
    "Door LED 1",
    "Door Membrane Switch",
    "Door Motion Sensor 1",
    "Door Distance Sensor 1",
    "Door Button 2",
    "Door Motion Sensor 2",
    "Door Distance Sensor 2",
    "Accelerometer X",
    "Accelerometer Y",
    "Accelerometer Z",
    "Gyroscope X",
    "Gyroscope Y",
    "Gyroscope Z",
    "Kitchen Button",
    "Temperature Kitchen",
    "Humidity Kitchen",
    "Kitchen Segment Display",
    "Temperature Bedroom",
    "Humidity Bedroom",
    "Temperature Master Bedroom",
    "Humidity Master Bedroom",
    "Living Room Motion Sensor",
    "Living Room Display",
    "Bedroom RGB",
    "Bedroom IR",
    "DMS PIN Entry",
]

# generate /live and /batch topics from base topics
MQTT_LIVE_TOPICS = [f"{topic}/live" for topic in MQTT_BASE_TOPICS]
MQTT_BATCH_TOPICS = [f"{topic}/batch" for topic in MQTT_BASE_TOPICS]
MQTT_TOPICS = MQTT_BASE_TOPICS + MQTT_LIVE_TOPICS + MQTT_BATCH_TOPICS

def clear_retained_messages():
    print_gray("Clearing retained MQTT messages...")
    clear_client = mqtt.Client()
    clear_client.connect("localhost", 1883, 60)
    
    # publish empty retained message to each topic to clear it
    for topic in MQTT_TOPICS:
        clear_client.publish(topic, payload="", retain=True)
    
    # also clear LED Control topic
    clear_client.publish("LED Control", payload="", retain=True)
    clear_client.disconnect()
    print_gray("Retained messages cleared.")

def on_connect(client, userdata, flags, rc):
    print_green(f"\n✅ Connected to MQTT broker (rc={rc})")
    # subscribe to all topics
    for topic in MQTT_TOPICS:
        client.subscribe(topic)
    print_gray(f"Subscribed to {len(MQTT_TOPICS)} topics")

def on_message(client, userdata, msg):
    # ignore empty messages (from clearing retained messages)
    if not msg.payload or msg.payload == b'':
        return
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        name = data.get("name", "")
        value = data.get("value", "")
        topic = msg.topic
        
        is_live = topic.endswith('/live')
        is_batch = topic.endswith('/batch')
        
        if is_live:
            # /live -> rules + state
            update_sensor_state(data)
            process_sensor_rules(data)
        elif is_batch:
            # /batch -> db only
            save_to_db(data)
        else:
            save_to_db(data)
            update_sensor_state(data)
            process_sensor_rules(data)
            
    except Exception as e:
        print_red(f"[ERROR] Processing message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# clear retained messages before starting
clear_retained_messages()

mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

print_green("\n" + "="*60)
print_green("🏠 SMART HOUSE SERVER STARTED")
print_green("🔒 Security System: ON (default)")
print_green(f"👥 Initial People Count: {people_count}")
print_green("="*60 + "\n")


# db functions
def save_to_db(data):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        value = data.get("value", "")
        
        point = (
            Point(data["measurement"])
            .tag("simulated", str(data.get("simulated", True)))
            .tag("runs_on", data.get("runs_on", ""))
            .tag("name", data.get("name", ""))
        )
        
        try:
            numeric_value = float(value)
            point = point.field("value", numeric_value)
        except (ValueError, TypeError):
            point = point.field("value_str", str(value))
            
            # for timer MM:SS -> seconds
            if ":" in str(value) and data.get("measurement") == "Kitchen Segment Display":
                try:
                    parts = str(value).split(":")
                    if len(parts) == 2:
                        mins = int(parts[0])
                        secs = int(parts[1])
                        total_seconds = mins * 60 + secs
                        point = point.field("value", float(total_seconds))
                    else:
                        point = point.field("value", 0.0)
                except (ValueError, IndexError):
                    point = point.field("value", 0.0)
            elif str(value).upper() in ["TRUE", "1", "DETECTED", "ACTIVE", "ON", "OPEN"]:
                point = point.field("value", 1.0)
            elif str(value).upper() in ["FALSE", "0", "NOT DETECTED", "INACTIVE", "OFF", "CLOSED"]:
                point = point.field("value", 0.0)
            else:
                # for other strings (like colors, PIN digits), just store string
                point = point.field("value", 0.0)
        
        write_api.write(bucket=bucket, org=org, record=point)
    except Exception as e:
        print_red(f"[DB ERROR] {e}")

def save_alarm_event(status, reason):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        status_value = 1.0 if status == "ACTIVATED" else 0.0
        
        point = (
            Point("Alarm Event")
            .tag("simulated", "False")
            .tag("runs_on", "SERVER")
            .tag("name", "ALARM")
            .tag("status", status)
            .field("value", status_value)
            .field("reason", reason)
        )
        
        write_api.write(bucket=bucket, org=org, record=point)
        print_gray(f"[DB] Alarm event saved: {status}")
    except Exception as e:
        print_red(f"[DB ERROR] Alarm event: {e}")

def update_sensor_state(data):
    global sensor_data
    with state_lock:
        name = data.get("name", "")
        value = data.get("value", "")
        if name:
            sensor_data[name] = value


# rules
def process_sensor_rules(data):
    global alarm_state, system_active, people_count, rgb_on, rgb_color
    
    name = data.get("name", "")
    value = data.get("value", "")
    
    # RULE 1: door sensor (DS1, DS2) - open > 5 seconds triggers ALARM
    if name in ["DS1", "DS2"]:
        check_door_open_alarm(name, value)
    
    # RULE 2: motion sensor (DPIR1) - turn on DL1 for 10 seconds
    if name == "DPIR1":
        if value == "detected":
            turn_on_dl1_for_10_seconds()
            check_entry_exit("DUS1", "DPIR1")
        elif value == "none":
            print_gray(f"🚶 [MOTION] {name} motion stopped")
    
    # RULE 3: motion sensor (DPIR2) - check entry/exit
    if name == "DPIR2":
        if value == "detected":
            check_entry_exit("DUS2", "DPIR2")
        elif value == "none":
            print_gray(f"🚶 [MOTION] {name} motion stopped")
    
    # RULE 4: distance sensor (DUS1, DUS2) - store history for entry/exit
    if name in ["DUS1", "DUS2"]:
        store_distance_history(name, value)
    
    # RULE 5: gyroscope (GSG) - significant movement triggers ALARM
    if name == "GSG" or "Gyroscope" in data.get("measurement", ""):
        check_gyroscope_alarm(data)
    
    # RULE 6: motion sensors (DPIR1, DPIR2, DPIR3) - ALARM if people_count == 0
    if name in ["DPIR1", "DPIR2", "DPIR3"]:
        if value == "detected":
            print_cyan(f"\n🚶 [MOTION] {name} detected movement!")
            check_motion_with_no_people(name)
        elif value == "none":
            print_gray(f"🚶 [MOTION] {name} motion stopped")
        
    # RULE 7: DMS PIN entry
    if name == "DMS" or "Membrane" in data.get("measurement", ""):
        process_dms_input(value)
    
    # RULE 8: DHT sensors - store for LCD rotation
    if name == "DHT1":
        store_dht_value("DHT1", data)
    elif name == "DHT2":
        store_dht_value("DHT2", data)
    elif name == "DHT3":
        store_dht_value("DHT3", data)

    # RULE 10: Kitchen Button - add N seconds to timer
    if name == "BTN" or "Kitchen Button" in data.get("measurement", ""):
        add_seconds_to_timer_from_button()

    # RULE 9: Bedroom RGB status sync
    if name == "BRGB":
        with state_lock:
            if value == "off":
                rgb_on = False
            else:
                rgb_on = True
                # value can be color name or "rgb(r,g,b)"
                if value.startswith("rgb("):
                    try:
                        parts = value.replace("rgb(", "").replace(")", "").split(",")
                        rgb_color["r"] = int(parts[0])
                        rgb_color["g"] = int(parts[1])
                        rgb_color["b"] = int(parts[2])
                    except:
                        pass
                else:
                    color_map = {
                        "red": {"r": 255, "g": 0, "b": 0},
                        "green": {"r": 0, "g": 255, "b": 0},
                        "blue": {"r": 0, "g": 0, "b": 255},
                        "yellow": {"r": 255, "g": 255, "b": 0},
                        "purple": {"r": 255, "g": 0, "b": 255},
                        "cyan": {"r": 0, "g": 255, "b": 255},
                        "white": {"r": 255, "g": 255, "b": 255},
                    }
                    if value in color_map:
                        rgb_color = color_map[value].copy()

    # store temperature/humidity from separate topics
    measurement = data.get("measurement", "")
    if "Temperature" in measurement:
        if "Bedroom" in measurement and "Master" not in measurement:
            dht_values["DHT1"]["temp"] = value
        elif "Master" in measurement:
            dht_values["DHT2"]["temp"] = value
        elif "Kitchen" in measurement:
            dht_values["DHT3"]["temp"] = value
    if "Humidity" in measurement:
        if "Bedroom" in measurement and "Master" not in measurement:
            dht_values["DHT1"]["humidity"] = value
        elif "Master" in measurement:
            dht_values["DHT2"]["humidity"] = value
        elif "Kitchen" in measurement:
            dht_values["DHT3"]["humidity"] = value


def check_door_open_alarm(door_name, value):
    global alarm_state, door_open_time
    
    should_deactivate = False
    is_door_open = str(value).upper() in ["TRUE", "1", "OPEN"]
    
    with state_lock:
        if is_door_open:
            # door is open - only start timer if system is active
            if door_open_time[door_name] is None and system_active:
                open_time = time.time()
                door_open_time[door_name] = open_time
                print_yellow(f"\n🚪 [DOOR] {door_name} OPENED - starting 5s alarm timer")
                # start a timer to check after 5 seconds, pass the open_time to verify it hasn't changed
                threading.Timer(5.1, check_door_timer, args=[door_name, open_time]).start()
            elif not system_active:
                print_gray(f"[DOOR] {door_name} opened (system OFF - no timer)")
        else:
            # door is closed - cancel timer and turn off alarm
            if door_open_time[door_name] is not None:
                print_green(f"\n🔒 [DOOR] {door_name} CLOSED - timer canceled")
            door_open_time[door_name] = None
            # if alarm is active, turn it off when door closes
            if alarm_state:
                should_deactivate = True
    
    # deactivate alarm OUTSIDE the lock to prevent deadlock
    if should_deactivate:
        deactivate_alarm(f"{door_name} closed")

def check_door_timer(door_name, original_open_time):
    global alarm_state, door_open_time, system_active
    
    should_trigger = False
    trigger_reason = ""
    with state_lock:
        current_open_time = door_open_time[door_name]
        
        # only trigger if same open event
        if current_open_time is not None and current_open_time == original_open_time:
            elapsed = time.time() - current_open_time
            if elapsed >= 5:
                if not alarm_state and system_active:
                    should_trigger = True
                    trigger_reason = f"{door_name} open for more than 5 seconds"
                elif not system_active:
                    print_gray(f"[DOOR] {door_name} open > 5s but system OFF - no alarm")
        else:
            print_gray(f"[DOOR] {door_name} timer expired but door was closed - no alarm")
    
    if should_trigger:
        trigger_alarm(trigger_reason)


def turn_on_dl1_for_10_seconds():
    global dl1_timer
    
    print_cyan("💡 [LED] DL1 ON for 10 seconds (motion detected)")
    # send MQTT command to turn on DL1
    mqtt_client.publish("LED Control", json.dumps({"command": "ON", "target": "DL1"}))
    
    # cancel previous timer if exists
    if dl1_timer is not None:
        dl1_timer.cancel()
    
    # set timer to turn off after 10 seconds
    dl1_timer = threading.Timer(10.0, turn_off_dl1)
    dl1_timer.start()

def turn_off_dl1():
    print_gray("[LED] DL1 OFF (timer expired)")
    mqtt_client.publish("LED Control", json.dumps({"command": "OFF", "target": "DL1"}))

def store_distance_history(sensor_name, value):
    global distance_history
    
    try:
        # parse distance value (remove 'cm' if present)
        if isinstance(value, str):
            value = value.replace("cm", "").strip()
        distance = float(value)
        
        with state_lock:
            distance_history[sensor_name].append({
                "distance": distance,
                "time": time.time()
            })
            # keep only last N readings
            if len(distance_history[sensor_name]) > DISTANCE_HISTORY_LIMIT:
                distance_history[sensor_name] = distance_history[sensor_name][-DISTANCE_HISTORY_LIMIT:]
            history_count = len(distance_history[sensor_name])
        
        # only print occasionally to reduce noise (every 5th reading)
        if history_count <= 2 or history_count % 5 == 0:
            print_gray(f"📏 [DISTANCE] {sensor_name}: {distance:.1f}cm")
    except ValueError:
        print_gray(f"[DISTANCE] Invalid distance value for {sensor_name}: {value}")


def check_entry_exit(dus_sensor, dpir_sensor):
    # uses last 2 distance readings to detect enter/exit
    global people_count, empty_house_acknowledged
    
    action = None  # "entered", "exited", or None
    current_count = 0
    prev_dist = 0
    curr_dist = 0
    
    with state_lock:
        history = distance_history.get(dus_sensor, [])
        if len(history) < 2:
            print_gray(f"[ENTRY/EXIT] {dus_sensor}: Not enough data ({len(history)}/2)")
            return  # not enough data
        
        # use only LAST 2 readings for easier direction detection
        prev_reading = history[-2]["distance"]  # second to last
        curr_reading = history[-1]["distance"]  # most recent
        prev_dist = prev_reading
        curr_dist = curr_reading
        
        # curr < prev = approaching = entering
        # curr > prev = moving away = exiting
        if curr_reading < prev_reading:
            # dist decreased = person approaching = entering
            people_count += 1
            current_count = people_count
            action = "entered"
            # reeset empty house flag when someone enters
            empty_house_acknowledged = False
        elif curr_reading > prev_reading:
            # dist increased = person moving away = exiting
            people_count = max(0, people_count - 1)
            current_count = people_count
            action = "exited"
            # if house is now empty, set the acknowledged flag
            # this means alarm will trigger on NEXT motion, not this one
            if people_count == 0:
                empty_house_acknowledged = True
                print_yellow(f"         ⚠️ House is now EMPTY - alarm will trigger on next motion")
    
    if action == "entered":
        print_green(f"\n🚶➡️🏠 [ENTRY] Person ENTERED via {dpir_sensor}/{dus_sensor}")
        print_green(f"         {prev_dist:.1f}cm → {curr_dist:.1f}cm | 👥 People: {current_count}")
        save_to_db({
            "measurement": "People Count",
            "simulated": False,
            "runs_on": "SERVER",
            "name": "PEOPLE_COUNT",
            "value": current_count
        })
    elif action == "exited":
        print_yellow(f"\n🏠➡️🚶 [EXIT] Person EXITED via {dpir_sensor}/{dus_sensor}")
        print_yellow(f"         {prev_dist:.1f}cm → {curr_dist:.1f}cm | 👥 People: {current_count}")
        save_to_db({
            "measurement": "People Count",
            "simulated": False,
            "runs_on": "SERVER",
            "name": "PEOPLE_COUNT",
            "value": current_count
        })


def check_gyroscope_alarm(data):
    global gyroscope_baseline, gyroscope_calibrated, alarm_state
    
    try:
        measurement = data.get("measurement", "")
        value = float(data.get("value", 0))
        
        if "Gyroscope X" in measurement:
            axis = "x"
        elif "Gyroscope Y" in measurement:
            axis = "y"
        elif "Gyroscope Z" in measurement:
            axis = "z"
        else:
            return
        
        should_trigger = False
        trigger_reason = ""
        
        with state_lock:
            if not gyroscope_calibrated:
                # calibrate baseline on first reading
                gyroscope_baseline[axis] = value
                if all(gyroscope_baseline.values()):
                    gyroscope_calibrated = True
                return
            
            # check for significant movement
            deviation = abs(value - gyroscope_baseline[axis])
            if deviation > GYROSCOPE_THRESHOLD:
                if not alarm_state and system_active:
                    should_trigger = True
                    trigger_reason = f"Gyroscope movement on {axis}-axis (deviation: {deviation:.1f})"
                elif not system_active:
                    print_gray(f"[GYRO] Movement detected but system OFF")
        
        if should_trigger:
            trigger_alarm(trigger_reason)
    except ValueError:
        pass


def check_motion_with_no_people(sensor_name):
    global alarm_state, people_count, system_active, empty_house_acknowledged
    
    should_trigger = False
    trigger_reason = ""
    current_people = 0
    current_alarm = False
    current_system = False
    is_acknowledged = False
    
    with state_lock:
        current_people = people_count
        current_alarm = alarm_state
        current_system = system_active
        is_acknowledged = empty_house_acknowledged
        
        # Only trigger alarm if:
        # 1. people_count == 0
        # 2. system is active
        # 3. alarm is not already active
        # 4. empty_house_acknowledged is True (meaning house was already empty BEFORE this motion)
        if people_count == 0 and system_active and not alarm_state:
            if empty_house_acknowledged:
                should_trigger = True
                trigger_reason = f"Motion detected by {sensor_name} with no people inside"
    
    print_gray(f"         👥 People count: {current_people}")
    
    # show why alarm is not triggered (for debugging)
    if current_people == 0 and current_system and current_alarm:
        print_gray(f"         ⚠️ (Alarm already active - not re-triggering)")
    elif current_people == 0 and current_system and not is_acknowledged:
        print_gray(f"         ⏳ (House just became empty - waiting for next motion to trigger alarm)")
    elif current_people > 0:
        print_gray(f"         ✅ (People inside - no alarm needed)")
    elif not current_system:
        print_gray(f"         🔓 (System OFF - no alarm)")
    
    if should_trigger:
        trigger_alarm(trigger_reason)


def process_dms_input(value):
    global entered_pin, alarm_state, system_active, system_activation_timer
    
    if value == "*":
        # clear entered PIN
        entered_pin = ""
        print_gray("[DMS] PIN cleared")
    elif value == "#":
        # submit PIN manually
        check_pin()
    elif len(value) == 1 and value.isdigit():
        # add digit to PIN
        entered_pin += value
        print_cyan(f"🔢 [DMS] PIN entry: {entered_pin} ({'*' * len(entered_pin)})")
        
        # auto-submit when PIN length matches expected PIN length
        if len(entered_pin) >= len(CORRECT_PIN):
            check_pin()

def check_pin():
    global entered_pin, alarm_state, system_active, system_activation_timer
    
    action = None  # "deactivate_alarm", "activate_system", "incorrect"
    
    with state_lock:
        if entered_pin == CORRECT_PIN:
            if alarm_state:
                # turn off ALARM
                alarm_state = False
                system_active = False
                action = "deactivate_alarm"
            else:
                # activate system after 10 seconds
                action = "activate_system"
                
                if system_activation_timer is not None:
                    system_activation_timer.cancel()
                
                system_activation_timer = threading.Timer(10.0, activate_security_system)
                system_activation_timer.start()
        else:
            action = "incorrect"
        
        entered_pin = ""
    
    if action == "deactivate_alarm":
        save_alarm_event("DEACTIVATED", "Correct PIN entered")
        mqtt_client.publish("Buzzer Control", json.dumps({"command": "OFF"}))
        print_green("\n✅ [DMS] Correct PIN - ALARM deactivated")
    elif action == "activate_system":
        print_cyan("\n⏳ [DMS] Correct PIN - System activating in 10 seconds...")
        mqtt_client.publish("DMS Feedback", json.dumps({"message": "System activating in 10 seconds"}))
    elif action == "incorrect":
        print_red("\n❌ [DMS] Incorrect PIN!")
        mqtt_client.publish("DMS Feedback", json.dumps({"message": "Incorrect PIN"}))


def activate_security_system():
    global system_active
    
    with state_lock:
        system_active = True
    print_green("\n🔒 [SYSTEM] SECURITY SYSTEM ACTIVATED!")
    mqtt_client.publish("DMS Feedback", json.dumps({"message": "System ACTIVE"}))
    save_alarm_event("SYSTEM_ACTIVATED", "PIN entered - system activated after 10 seconds")

def trigger_alarm(reason):
    global alarm_state
    
    should_trigger = False
    with state_lock:
        if not alarm_state:
            alarm_state = True
            should_trigger = True
    
    if should_trigger:
        print_red(f"\n{'='*60}")
        print_red(f"🚨🚨🚨 ALARM TRIGGERED 🚨🚨🚨")
        print_red(f"Reason: {reason}")
        print_red(f"{'='*60}")
        save_alarm_event("ACTIVATED", reason)
        # turn on buzzer
        mqtt_client.publish("Buzzer Control", json.dumps({"command": "ON"}))


def deactivate_alarm(reason):
    global alarm_state
    
    should_deactivate = False
    with state_lock:
        if alarm_state:
            alarm_state = False
            should_deactivate = True
    
    if should_deactivate:
        print_green(f"\n{'='*60}")
        print_green(f"🔕 ALARM DEACTIVATED")
        print_green(f"Reason: {reason}")
        print_green(f"{'='*60}")
        save_alarm_event("DEACTIVATED", reason)
        # turn off buzzer
        mqtt_client.publish("Buzzer Control", json.dumps({"command": "OFF"}))


def add_seconds_to_timer_from_button():
    global timer_seconds, timer_blinking, timer_just_set
    
    action = None  # "add_time" or "stop_blinking"
    current_seconds = 0
    add_amount = 0
    
    with state_lock:
        if timer_blinking:
            # timer finished and blinking - just stop the blinking, don't add time
            timer_blinking = False
            action = "stop_blinking"
        elif timer_seconds > 0:
            # timer active - add configured seconds
            timer_seconds += timer_add_seconds
            timer_just_set = True
            current_seconds = timer_seconds
            add_amount = timer_add_seconds
            action = "add_time"
        # if timer_seconds == 0 and not blinking, button press does nothing

    if action == "stop_blinking":
        mqtt_client.publish("Timer Display", json.dumps({"command": "STOP_BLINK"}))
        print_cyan(f"🔘 [BTN] Kitchen Button pressed - stopped blinking")
    elif action == "add_time":
        minutes = current_seconds // 60
        seconds = current_seconds % 60
        mqtt_client.publish("Timer Display", json.dumps({
            "command": "SET",
            "value": f"{minutes:02d}:{seconds:02d}"
        }))
        print_cyan(f"🔘 [BTN] Kitchen Button pressed - added {add_amount}s → {minutes:02d}:{seconds:02d}")


def store_dht_value(dht_name, data):
    global dht_values
    
    value = data.get("value", "")
    # parse if it's a combined format like "25.5°C 60%"
    if "°C" in str(value) or "%" in str(value):
        parts = str(value).split()
        for part in parts:
            if "°C" in part:
                dht_values[dht_name]["temp"] = part.replace("°C", "")
            elif "%" in part:
                dht_values[dht_name]["humidity"] = part.replace("%", "")


# background tasks
def lcd_rotation_task():
    current_dht = 0
    dht_names = ["DHT1", "DHT2", "DHT3"]
    
    while True:
        try:
            dht_name = dht_names[current_dht]
            temp = dht_values[dht_name]["temp"]
            humidity = dht_values[dht_name]["humidity"]
            
            # send to LCD display
            message = f"{dht_name}: {temp}C {humidity}%"
            mqtt_client.publish("LCD Control", json.dumps({
                "command": "DISPLAY",
                "message": message
            }))
            
            current_dht = (current_dht + 1) % 3
        except Exception as e:
            print(f"LCD rotation error: {e}")
        
        time.sleep(5)  # rotate every 5 seconds

def print_rainbow(message):
    colors = [Colors.RED, Colors.YELLOW, Colors.CYAN]
    result = ""
    for i, char in enumerate(message):
        result += colors[i % len(colors)] + char
    print(result + Colors.ENDC)

def print_separator():
    print_gray("-" * 60)

def print_with_timestamp(color, text):
    import time
    t = time.localtime()
    timestamp = time.strftime('%H:%M:%S', t)
    print()
    print(f"{color}{text}{Colors.ENDC}  {Colors.GRAY}[{timestamp}]{Colors.ENDC}")
    print_separator()

def timer_countdown_task():
    global timer_seconds, timer_blinking, timer_just_set
    
    blink_announced = False
    
    while True:
        try:
            should_publish_update = False
            should_publish_blink = False
            display_value = None
            current_seconds = 0
            
            with state_lock:
                # skip decrement if timer was just set/modified (prevents losing 1 second)
                if timer_just_set:
                    timer_just_set = False
                    current_seconds = timer_seconds
                elif timer_seconds > 0 and not timer_blinking:
                    timer_seconds -= 1
                    current_seconds = timer_seconds
                    
                    # prepare update for 4SD display
                    minutes = timer_seconds // 60
                    seconds = timer_seconds % 60
                    display_value = f"{minutes:02d}:{seconds:02d}"
                    should_publish_update = True
                    
                    if timer_seconds == 0:
                        timer_blinking = True
                        should_publish_blink = True
                elif timer_blinking:
                    current_seconds = 0
            
            # print only last 5 seconds
            if should_publish_update and current_seconds <= 5 and current_seconds > 0:
                print_cyan(f"⏱️ [TIMER] {display_value}")
            
            # publish MQTT messages to PI2's 4SD display
            if should_publish_update:
                mqtt_client.publish("Timer Display", json.dumps({
                    "command": "SET",
                    "value": display_value
                }))
            
            if should_publish_blink:
                print_rainbow("🎉🎉🎉 [TIMER] FINISHED - 4SD BLINKING! 🎉🎉🎉")
                blink_announced = True
                mqtt_client.publish("Timer Display", json.dumps({
                    "command": "BLINK",
                    "value": "00:00"
                }))
            
            # reset blink announced when timer restarted
            if not timer_blinking:
                blink_announced = False
                
        except Exception as e:
            print(f"Timer countdown error: {e}")
        
        time.sleep(1)

def status_display_task():
    """Background task to periodically display system status"""
    global people_count, alarm_state, system_active
    
    while True:
        try:
            time.sleep(30)  # every 30 seconds
            with state_lock:
                current_people = people_count
                current_alarm = alarm_state
                current_system = system_active
            
            status_emoji = "🚨" if current_alarm else "✅"
            system_emoji = "🔒" if current_system else "🔓"
            print_blue(f"\n{'─'*40}")
            print_blue(f"📊 [STATUS] {status_emoji} Alarm: {'ACTIVE' if current_alarm else 'OFF'} | {system_emoji} System: {'ON' if current_system else 'OFF'} | 👥 People: {current_people}")
            print_blue(f"{'─'*40}")
        except Exception as e:
            pass
        

# start background tasks
lcd_thread = threading.Thread(target=lcd_rotation_task, daemon=True)
lcd_thread.start()

timer_thread = threading.Thread(target=timer_countdown_task, daemon=True)
timer_thread.start()

status_thread = threading.Thread(target=status_display_task, daemon=True)
status_thread.start()


# ---- API ROUTES ----

# route to store dummy data
@app.route('/store_data', methods=['POST'])
def store_data():
    try:
        data = request.get_json()
        save_to_db(data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def handle_influx_query(query):
    try:
        query_api = influxdb_client.query_api()
        tables = query_api.query(query, org=org)

        container = []
        for table in tables:
            for record in table.records:
                container.append(record.values)

        return jsonify({"status": "success", "data": container})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/aggregate_query', methods=['GET'])
def retrieve_aggregate_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r.name == "Door Button 1")"""
    return handle_influx_query(query)


# ---- STATUS ENDPOINT ----
@app.route('/status', methods=['GET'])
def get_status():
    global alarm_state, system_active, people_count, sensor_data
    with state_lock:
        return jsonify({
            "alarm": alarm_state,
            "system_active": system_active,
            "people_count": people_count,
            "timer_seconds": timer_seconds,
            "timer_blinking": timer_blinking,
            "rgb_on": rgb_on,
            "rgb_color": rgb_color,
            "sensors": sensor_data.copy(),
            "dht_values": dht_values.copy()
        })

# ---- ALARM ENDPOINTS ----
@app.route('/alarm/deactivate', methods=['POST'])
def api_deactivate_alarm():
    global alarm_state, system_active
    with state_lock:
        alarm_state = False
        system_active = False
    # publish to MQTT to turn off buzzer
    mqtt_client.publish("Buzzer Control", json.dumps({"command": "OFF"}))
    save_alarm_event("DEACTIVATED", "Deactivated via Web App")
    return jsonify({"status": "success", "alarm": False})

@app.route('/alarm/trigger', methods=['POST'])
def manual_trigger_alarm():
    """Manually trigger alarm (for testing)"""
    data = request.get_json()
    reason = data.get("reason", "Manual trigger via Web App")
    trigger_alarm(reason)
    return jsonify({"status": "success", "alarm": True})

@app.route('/system/activate', methods=['POST'])
def activate_system():
    global system_active
    with state_lock:
        system_active = True
    print("🔒 SECURITY SYSTEM: ON")
    save_alarm_event("SYSTEM_ACTIVATED", "Activated via Web App")
    return jsonify({"status": "success", "system_active": True})

@app.route('/system/deactivate', methods=['POST'])
def deactivate_system():
    global system_active
    with state_lock:
        system_active = False
    print("🔓 SECURITY SYSTEM: OFF")
    save_alarm_event("SYSTEM_DEACTIVATED", "Deactivated via Web App")
    return jsonify({"status": "success", "system_active": False})


# ---- TIMER ENDPOINTS ----
@app.route('/timer/set', methods=['POST'])
def set_timer():
    global timer_seconds, timer_blinking, timer_just_set
    data = request.get_json()
    
    with state_lock:
        timer_seconds = data.get("seconds", 0)
        timer_blinking = False
        timer_just_set = True  # Skip next countdown decrement
        current_timer_seconds = timer_seconds
    
    # publish to MQTT for 4SD display (outside lock to prevent deadlock)
    minutes = current_timer_seconds // 60
    seconds = current_timer_seconds % 60
    mqtt_client.publish("Timer Display", json.dumps({
        "command": "SET",
        "value": f"{minutes:02d}:{seconds:02d}"
    }))
    return jsonify({"status": "success", "seconds": current_timer_seconds})

@app.route('/timer/configure', methods=['POST'])
def configure_timer():
    global timer_add_seconds
    data = request.get_json()
    
    with state_lock:
        timer_add_seconds = data.get("add_seconds", 10)
        current_add_seconds = timer_add_seconds
    
    # publish to MQTT for BTN configuration (outside lock to prevent deadlock)
    mqtt_client.publish("Timer Control", json.dumps({"command": "CONFIGURE", "add_seconds": current_add_seconds}))
    return jsonify({"status": "success", "add_seconds": current_add_seconds})

@app.route('/timer/add', methods=['POST'])
def add_timer_seconds():
    """Add N seconds to timer (simulates BTN press)"""
    global timer_seconds, timer_blinking, timer_just_set
    
    was_blinking = False
    current_timer_seconds = 0
    
    with state_lock:
        if timer_blinking:
            timer_blinking = False
            was_blinking = True
        timer_seconds += timer_add_seconds
        timer_just_set = True  # Skip next countdown decrement
        current_timer_seconds = timer_seconds
    
    if was_blinking:
        mqtt_client.publish("Timer Display", json.dumps({"command": "STOP_BLINK"}))
    
    minutes = current_timer_seconds // 60
    seconds = current_timer_seconds % 60
    mqtt_client.publish("Timer Display", json.dumps({
        "command": "SET",
        "value": f"{minutes:02d}:{seconds:02d}"
    }))
    return jsonify({"status": "success", "seconds": current_timer_seconds})

@app.route('/timer/stop', methods=['POST'])
def stop_timer():
    global timer_blinking
    with state_lock:
        timer_blinking = False
    mqtt_client.publish("Timer Display", json.dumps({"command": "STOP_BLINK"}))
    return jsonify({"status": "success"})

@app.route('/timer/reset', methods=['POST'])
def reset_timer():
    """Reset timer to 00:00"""
    global timer_seconds, timer_blinking
    with state_lock:
        timer_seconds = 0
        timer_blinking = False
    mqtt_client.publish("Timer Display", json.dumps({
        "command": "SET",
        "value": "00:00"
    }))
    return jsonify({"status": "success", "seconds": 0})


# ---- RGB ENDPOINTS ----
@app.route('/rgb/on', methods=['POST'])
def rgb_turn_on():
    global rgb_on
    with state_lock:
        rgb_on = True
    mqtt_client.publish("RGB Control", json.dumps({"command": "ON", "color": rgb_color}))
    return jsonify({"status": "success", "rgb_on": True})

@app.route('/rgb/off', methods=['POST'])
def rgb_turn_off():
    global rgb_on
    with state_lock:
        rgb_on = False
    mqtt_client.publish("RGB Control", json.dumps({"command": "OFF"}))
    return jsonify({"status": "success", "rgb_on": False})

@app.route('/rgb/color', methods=['POST'])
def rgb_set_color():
    global rgb_color, rgb_on
    data = request.get_json()
    with state_lock:
        rgb_color = {
            "r": data.get("r", 255),
            "g": data.get("g", 0),
            "b": data.get("b", 0)
        }
        rgb_on = True
    mqtt_client.publish("RGB Control", json.dumps({"command": "COLOR", "color": rgb_color}))
    return jsonify({"status": "success", "color": rgb_color})


# ---- PEOPLE COUNT ENDPOINT ----
@app.route('/people/count', methods=['GET'])
def get_people_count():
    global people_count
    with state_lock:
        return jsonify({"count": people_count})

@app.route('/people/set', methods=['POST'])
def set_people_count():
    """Manually set people count (for testing)"""
    global people_count
    data = request.get_json()
    with state_lock:
        people_count = data.get("count", 0)
    return jsonify({"status": "success", "count": people_count})

# ---- DHT VALUES ENDPOINT ----
@app.route('/dht/values', methods=['GET'])
def get_dht_values():
    """Get current DHT sensor values"""
    return jsonify(dht_values)

# ---- ALARM EVENTS ENDPOINT ----
@app.route('/alarm/events', methods=['GET'])
def get_alarm_events():
    """Get recent alarm events from database"""
    query = f"""from(bucket: "{bucket}")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "Alarm Event")
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 50)"""
    return handle_influx_query(query)


# ---- DATA MANAGEMENT ENDPOINTS ----
@app.route('/data/delete/<pi_name>', methods=['DELETE'])
def delete_pi_data(pi_name):
    """Delete all InfluxDB data for a specific PI (PI1, PI2, PI3)"""
    try:
        delete_api = influxdb_client.delete_api()
        
        # Delete data where runs_on tag matches the PI name
        start = "1970-01-01T00:00:00Z"
        stop = datetime.utcnow().isoformat() + "Z"
        
        delete_api.delete(
            start=start,
            stop=stop,
            predicate=f'runs_on="{pi_name}"',
            bucket=bucket,
            org=org
        )
        
        print(f"🗑️ Deleted all data for {pi_name}")
        return jsonify({"status": "success", "message": f"Deleted all data for {pi_name}"})
    except Exception as e:
        print(f"Error deleting data for {pi_name}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/data/delete/all', methods=['DELETE'])
def delete_all_data():
    """Delete all InfluxDB data"""
    try:
        delete_api = influxdb_client.delete_api()
        
        start = "1970-01-01T00:00:00Z"
        stop = datetime.utcnow().isoformat() + "Z"
        
        # Delete all data from bucket
        delete_api.delete(
            start=start,
            stop=stop,
            predicate='_measurement != ""',
            bucket=bucket,
            org=org
        )
        
        print("🗑️ Deleted ALL InfluxDB data")
        return jsonify({"status": "success", "message": "Deleted all data"})
    except Exception as e:
        print(f"Error deleting all data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/data/delete/server', methods=['DELETE'])
def delete_server_data():
    """Delete all server-generated data (alarm events, people count)"""
    try:
        delete_api = influxdb_client.delete_api()
        
        start = "1970-01-01T00:00:00Z"
        stop = datetime.utcnow().isoformat() + "Z"
        
        delete_api.delete(
            start=start,
            stop=stop,
            predicate='runs_on="SERVER"',
            bucket=bucket,
            org=org
        )
        
        print("🗑️ Deleted all SERVER data")
        return jsonify({"status": "success", "message": "Deleted server data"})
    except Exception as e:
        print(f"Error deleting server data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False, threaded=True)
