from flask import Flask, jsonify, request
from flask_cors import CORS
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime


app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization", "X-Requested-With"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


# InfluxDB Configuration
token = "MnETT6nOjyevCYF5obDzluansp1gyd1w9JbFSutVKUIXNtV6S8EaUeE-LBbMQ7pGUzTpJCJTP39jdks5TlyZoQ=="
org = "iot"
url = "http://localhost:8086"
bucket = "iot"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)


# ---- GLOBAL STATES ----
alarm_state = False
system_active = True  # security system is ON at start
people_count = 0
timer_seconds = 0
timer_add_seconds = 10
timer_blinking = False
rgb_on = False
rgb_color = {"r": 255, "g": 0, "b": 0}
sensor_data = {}
state_lock = threading.Lock()

# security PIN code
CORRECT_PIN = "2110"
entered_pin = ""
system_activation_timer = None

# door open tracking for ALARM (DS1, DS2 open > 5 seconds)
door_open_time = {"DS1": None, "DS2": None}

# distance history for people counting (entry/exit detection)
distance_history = {"DUS1": [], "DUS2": []}
DISTANCE_HISTORY_LIMIT = 10  # keep last 10 readings
ENTRY_EXIT_THRESHOLD = 50  # cm - threshold to detect entry/exit

# motion detection tracking for DL1 auto-off
dl1_timer = None

# gyroscope baseline for significant movement detection
gyroscope_baseline = {"x": 0, "y": 0, "z": 0}
gyroscope_calibrated = False
GYROSCOPE_THRESHOLD = 30  # degrees per second - significant movement

# DHT values for LCD rotation
dht_values = {
    "DHT1": {"temp": 0, "humidity": 0},
    "DHT2": {"temp": 0, "humidity": 0},
    "DHT3": {"temp": 0, "humidity": 0}
}


# ---- MQTT CONFIGURATION ----
mqtt_client = mqtt.Client()

# list of all topics to subscribe to
MQTT_TOPICS = [
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

def clear_retained_messages():
    """Clear all retained messages from MQTT broker on server start"""
    print("Clearing retained MQTT messages...")
    clear_client = mqtt.Client()
    clear_client.connect("localhost", 1883, 60)
    
    # publish empty retained message to each topic to clear it
    for topic in MQTT_TOPICS:
        clear_client.publish(topic, payload="", retain=True)
    
    # also clear LED Control topic
    clear_client.publish("LED Control", payload="", retain=True)
    
    clear_client.disconnect()
    print("Retained messages cleared.")

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    # subscribe to all topics
    for topic in MQTT_TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    # ignore empty messages (from clearing retained messages)
    if not msg.payload or msg.payload == b'':
        return
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        name = data.get("name", "")
        value = data.get("value", "")
        # Debug print for DS1 and DPIR1
        if name in ["DS1", "DPIR1"]:
            print(f"[SERVER] Received: {name} = {value}")
        save_to_db(data)
        update_sensor_state(data)
        # process rules based on sensor data
        process_sensor_rules(data)
    except Exception as e:
        print(f"Error processing message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# clear retained messages before starting
clear_retained_messages()

mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

print("🔒 SECURITY SYSTEM: ON (default at startup)")


# ---- DB FUNCTIONS ----
def save_to_db(data):
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point(data["measurement"])
            .tag("simulated", str(data.get("simulated", True)))
            .tag("runs_on", data.get("runs_on", ""))
            .tag("name", data.get("name", ""))
            .field("measurement", str(data.get("value", "")))
        )
        write_api.write(bucket=bucket, org=org, record=point)
    except Exception as e:
        print(f"Error saving to DB: {e}")

def save_alarm_event(event_type, reason):
    """Save alarm events (entry/exit) to DB"""
    try:
        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point("Alarm Event")
                .tag("event_type", event_type)
                .tag("reason", reason)
                .field("timestamp", datetime.now().isoformat())
                .field("event", event_type)
        )
        write_api.write(bucket=bucket, org=org, record=point)
        print(f"ALARM EVENT: {event_type} - {reason}")
    except Exception as e:
        print(f"Error saving alarm event: {e}")

def update_sensor_state(data):
    global sensor_data
    with state_lock:
        name = data.get("name", "")
        value = data.get("value", "")
        if name:
            sensor_data[name] = value


# ---- RULES ----
def process_sensor_rules(data):
    """Main function to process all sensor rules"""
    global alarm_state, system_active, people_count
    
    name = data.get("name", "")
    value = data.get("value", "")
    
    # RULE 1: door sensor (DS1, DS2) - open > 5 seconds triggers ALARM
    if name in ["DS1", "DS2"]:
        check_door_open_alarm(name, value)
    
    # RULE 2: motion sensor (DPIR1) - turn on DL1 for 10 seconds
    if name == "DPIR1" and value == "detected":
        turn_on_dl1_for_10_seconds()
        check_entry_exit("DUS1", "DPIR1")
    
    # RULE 3: motion sensor (DPIR2) - check entry/exit
    if name == "DPIR2" and value == "detected":
        check_entry_exit("DUS2", "DPIR2")
    
    # RULE 4: distance sensor (DUS1, DUS2) - store history for entry/exit
    if name in ["DUS1", "DUS2"]:
        store_distance_history(name, value)
    
    # RULE 5: gyroscope (GSG) - significant movement triggers ALARM
    if name == "GSG" or "Gyroscope" in data.get("measurement", ""):
        check_gyroscope_alarm(data)
    
    # RULE 6: motion sensors (DPIR1, DPIR2, DPIR3) - ALARM if people_count == 0
    if name in ["DPIR1", "DPIR2", "DPIR3"] and value == "detected":
        check_motion_with_no_people(name)
    
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
    """RULE: If DS1 or DS2 is open for more than 5 seconds, trigger ALARM"""
    global alarm_state, door_open_time
    
    print(f"[RULE] check_door_open_alarm: {door_name} = {value}")
    
    with state_lock:
        if value == "TRUE" or value == "1" or value == True:
            # door is open
            if door_open_time[door_name] is None:
                door_open_time[door_name] = time.time()
                print(f"[RULE] {door_name} opened - starting 5 second timer")
                # start a timer to check after 5 seconds
                threading.Timer(5.1, check_door_timer, args=[door_name]).start()
        else:
            # door is closed
            print(f"[RULE] {door_name} closed - canceling alarm timer")
            door_open_time[door_name] = None
            # if alarm was triggered by this door, turn it off
            if alarm_state:
                print(f"{door_name} closed - checking if alarm should turn off")

def check_door_timer(door_name):
    """Check if door is still open after 5 seconds"""
    global alarm_state, door_open_time, system_active
    
    should_trigger = False
    trigger_reason = ""
    with state_lock:
        if door_open_time[door_name] is not None:
            elapsed = time.time() - door_open_time[door_name]
            if elapsed >= 5:
                if not alarm_state and system_active:
                    should_trigger = True
                    trigger_reason = f"{door_name} open for more than 5 seconds"
                elif not system_active:
                    print(f"[RULE] {door_name} open > 5s but system is OFF - no alarm")
    
    if should_trigger:
        trigger_alarm(trigger_reason)


def turn_on_dl1_for_10_seconds():
    """RULE: When DPIR1 detects motion, turn on DL1 for 10 seconds"""
    global dl1_timer
    
    print("DPIR1 detected motion - turning on DL1 for 10 seconds")
    # send MQTT command to turn on DL1
    mqtt_client.publish("LED Control", json.dumps({"command": "ON", "target": "DL1"}))
    
    # cancel previous timer if exists
    if dl1_timer is not None:
        dl1_timer.cancel()
    
    # set timer to turn off after 10 seconds
    dl1_timer = threading.Timer(10.0, turn_off_dl1)
    dl1_timer.start()

def turn_off_dl1():
    print("Turning off DL1")
    mqtt_client.publish("LED Control", json.dumps({"command": "OFF", "target": "DL1"}))

def store_distance_history(sensor_name, value):
    """Store distance reading for entry/exit detection"""
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
    except ValueError:
        print("Invalid distance value - store_distance_history()")


def check_entry_exit(dus_sensor, dpir_sensor):
    """RULE: Determine if person is entering or exiting based on distance history"""
    global people_count
    
    action = None  # "entered", "exited", or None
    current_count = 0
    
    with state_lock:
        history = distance_history.get(dus_sensor, [])
        if len(history) < 3:
            print("Not enough data - check_entry_exit()")
            return  # not enough data
        
        # get recent readings (last 3 seconds)
        recent_time = time.time() - 3
        recent_readings = [r for r in history if r["time"] > recent_time]
        
        if len(recent_readings) < 2:
            print("Recent readins < 2 - check_entry_exit()")
            return
        
        # calculate if distance is decreasing (entering) or increasing (exiting)
        first_reading = recent_readings[0]["distance"]
        last_reading = recent_readings[-1]["distance"]
        
        if first_reading > last_reading and first_reading - last_reading > 20:
            # dist decreasing = person entering
            people_count += 1
            current_count = people_count
            action = "entered"
        elif last_reading > first_reading and last_reading - first_reading > 20:
            # dist increasing = person exiting
            people_count = max(0, people_count - 1)
            current_count = people_count
            action = "exited"
    
    if action == "entered":
        print(f"Person ENTERED via {dpir_sensor}. People count: {current_count}")
        save_to_db({
            "measurement": "People Count",
            "simulated": False,
            "runs_on": "SERVER",
            "name": "PEOPLE_COUNT",
            "value": current_count
        })
    elif action == "exited":
        print(f"Person EXITED via {dpir_sensor}. People count: {current_count}")
        save_to_db({
            "measurement": "People Count",
            "simulated": False,
            "runs_on": "SERVER",
            "name": "PEOPLE_COUNT",
            "value": current_count
        })


def check_gyroscope_alarm(data):
    """RULE: If GSG detects significant movement, trigger ALARM"""
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
                    trigger_reason = f"Significant gyroscope movement detected on {axis}-axis (deviation: {deviation:.2f})"
                elif not system_active:
                    print(f"[RULE] Gyroscope movement detected but system is OFF - no alarm")
        
        if should_trigger:
            trigger_alarm(trigger_reason)
    except ValueError:
        print("ValueError - check_gyroscope_alarm()")


def check_motion_with_no_people(sensor_name):
    """RULE: If people_count == 0 and motion detected, trigger ALARM"""
    global alarm_state, people_count, system_active
    
    should_trigger = False
    trigger_reason = ""
    
    with state_lock:
        if people_count == 0 and system_active:
            if not alarm_state:
                should_trigger = True
                trigger_reason = f"Motion detected by {sensor_name} with no people inside"
    
    # Call trigger_alarm OUTSIDE the lock to prevent nested lock deadlock
    if should_trigger:
        trigger_alarm(trigger_reason)


def process_dms_input(value):
    """Process input from Door Membrane Switch (PIN keypad)"""
    global entered_pin, alarm_state, system_active, system_activation_timer
    
    if value == "*":
        # clear entered PIN
        entered_pin = ""
        print("DMS: PIN cleared")
    elif value == "#":
        # submit PIN
        check_pin()
    elif len(value) == 1 and value.isdigit():
        # add digit to PIN
        entered_pin += value
        print(f"DMS: PIN entry: {'*' * len(entered_pin)}")
        
        # auto-submit on 4 digits
        if len(entered_pin) >= 4:
            check_pin()

def check_pin():
    """Check if entered PIN is correct"""
    global entered_pin, alarm_state, system_active, system_activation_timer
    
    action = None  # "deactivate_alarm", "activate_system", "incorrect"
    
    with state_lock:
        if entered_pin == CORRECT_PIN:
            print("DMS: Correct PIN entered!")
            
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
        print("ALARM deactivated by PIN")
    elif action == "activate_system":
        print("System will activate in 10 seconds...")
        mqtt_client.publish("DMS Feedback", json.dumps({"message": "System activating in 10 seconds"}))
    elif action == "incorrect":
        print("DMS: Incorrect PIN!")
        mqtt_client.publish("DMS Feedback", json.dumps({"message": "Incorrect PIN"}))


def activate_security_system():
    """Activate the security system after delay"""
    global system_active
    
    with state_lock:
        system_active = True
    print("-- SECURITY SYSTEM ACTIVATED!")
    mqtt_client.publish("DMS Feedback", json.dumps({"message": "System ACTIVE"}))
    save_alarm_event("SYSTEM_ACTIVATED", "PIN entered - system activated after 10 seconds")

def trigger_alarm(reason):
    """Trigger the ALARM state"""
    global alarm_state
    
    should_trigger = False
    with state_lock:
        if not alarm_state:
            alarm_state = True
            should_trigger = True
    
    if should_trigger:
        print(f"!!! ALARM TRIGGERED: {reason} !!!")
        save_alarm_event("ACTIVATED", reason)
        # turn on buzzer
        mqtt_client.publish("Buzzer Control", json.dumps({"command": "ON"}))


def store_dht_value(dht_name, data):
    """Store DHT temperature/humidity values"""
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


# ---- BACKGROUND TASKS ----
def lcd_rotation_task():
    """Background task to rotate DHT values on LCD display"""
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

def timer_countdown_task():
    """Background task to handle kitchen timer countdown"""
    global timer_seconds, timer_blinking
    
    while True:
        try:
            # capture state under lock, then release before MQTT calls to prevent deadlock
            should_publish_update = False
            should_publish_blink = False
            display_value = None
            
            with state_lock:
                if timer_seconds > 0 and not timer_blinking:
                    timer_seconds -= 1
                    
                    # prepare update for 4SD display
                    minutes = timer_seconds // 60
                    seconds = timer_seconds % 60
                    display_value = f"{minutes:02d}:{seconds:02d}"
                    should_publish_update = True
                    
                    if timer_seconds == 0:
                        timer_blinking = True
                        should_publish_blink = True
            
            # publish MQTT messages OUTSIDE the lock to prevent deadlock
            if should_publish_update:
                mqtt_client.publish("Timer Display", json.dumps({
                    "command": "SET",
                    "value": display_value
                }))
            
            if should_publish_blink:
                mqtt_client.publish("Timer Display", json.dumps({
                    "command": "BLINK",
                    "value": "00:00"
                }))
        except Exception as e:
            print(f"Timer countdown error: {e}")
        
        time.sleep(1)

# start background tasks
lcd_thread = threading.Thread(target=lcd_rotation_task, daemon=True)
lcd_thread.start()

timer_thread = threading.Thread(target=timer_countdown_task, daemon=True)
timer_thread.start()


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
def deactivate_alarm():
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
    global timer_seconds, timer_blinking
    data = request.get_json()
    
    with state_lock:
        timer_seconds = data.get("seconds", 0)
        timer_blinking = False
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
    global timer_seconds, timer_blinking
    
    was_blinking = False
    current_timer_seconds = 0
    
    with state_lock:
        if timer_blinking:
            timer_blinking = False
            was_blinking = True
        timer_seconds += timer_add_seconds
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False, threaded=True)
