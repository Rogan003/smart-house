from flask import Flask, jsonify, request
from flask_cors import CORS
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import threading


app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend


# InfluxDB Configuration
token = "MnETT6nOjyevCYF5obDzluansp1gyd1w9JbFSutVKUIXNtV6S8EaUeE-LBbMQ7pGUzTpJCJTP39jdks5TlyZoQ=="
org = "iot"
url = "http://localhost:8086"
bucket = "iot"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)


# Global state
alarm_state = False
system_active = False
people_count = 0
timer_seconds = 0
timer_add_seconds = 10
timer_blinking = False
rgb_on = False
rgb_color = {"r": 255, "g": 0, "b": 0}
sensor_data = {}
state_lock = threading.Lock()


# MQTT Configuration
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    client.subscribe("Door Button 1")
    client.subscribe("Door Buzzer 1")
    client.subscribe("Door LED 1")
    client.subscribe("Door Membrane Switch")
    client.subscribe("Door Motion Sensor 1")
    client.subscribe("Door Distance Sensor 1")
    client.subscribe("Door Button 2")
    client.subscribe("Door Motion Sensor 2")
    client.subscribe("Door Distance Sensor 2")
    client.subscribe("Accelerometer X")
    client.subscribe("Accelerometer Y")
    client.subscribe("Accelerometer Z")
    client.subscribe("Gyroscope X")
    client.subscribe("Gyroscope Y")
    client.subscribe("Gyroscope Z")
    client.subscribe("Kitchen Button")
    client.subscribe("Temperature Kitchen")
    client.subscribe("Humidity Kitchen")
    client.subscribe("Kitchen Segment Display")
    client.subscribe("Temperature Bedroom")
    client.subscribe("Humidity Bedroom")
    client.subscribe("Temperature Master Bedroom")
    client.subscribe("Humidity Master Bedroom")
    client.subscribe("Living Room Motion Sensor")
    client.subscribe("Living Room Display")
    client.subscribe("Bedroom RGB")
    client.subscribe("Bedroom IR")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        save_to_db(data)
        update_sensor_state(data)
    except Exception as e:
        print(f"Error processing message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()


def save_to_db(data):
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    point = (
        Point(data["measurement"])
        .tag("simulated", data["simulated"])
        .tag("runs_on", data["runs_on"])
        .tag("name", data["name"])
        .field("measurement", data["value"])
    )
    write_api.write(bucket=bucket, org=org, record=point)


def update_sensor_state(data):
    global sensor_data
    with state_lock:
        name = data.get("name", "")
        value = data.get("value", "")
        if name:
            sensor_data[name] = value


# Route to store dummy data
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


# ========== STATUS ENDPOINT ==========
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
            "sensors": sensor_data.copy()
        })


# ========== ALARM ENDPOINTS ==========
@app.route('/alarm/deactivate', methods=['POST'])
def deactivate_alarm():
    global alarm_state
    with state_lock:
        alarm_state = False
    # Publish to MQTT to turn off buzzer
    mqtt_client.publish("Buzzer Control", json.dumps({"command": "OFF"}))
    return jsonify({"status": "success", "alarm": False})


@app.route('/system/activate', methods=['POST'])
def activate_system():
    global system_active
    with state_lock:
        system_active = True
    return jsonify({"status": "success", "system_active": True})


@app.route('/system/deactivate', methods=['POST'])
def deactivate_system():
    global system_active
    with state_lock:
        system_active = False
    return jsonify({"status": "success", "system_active": False})


# ========== TIMER ENDPOINTS ==========
@app.route('/timer/set', methods=['POST'])
def set_timer():
    global timer_seconds, timer_blinking
    data = request.get_json()
    with state_lock:
        timer_seconds = data.get("seconds", 0)
        timer_blinking = False
    # Publish to MQTT for 4SD display
    mqtt_client.publish("Timer Control", json.dumps({"command": "SET", "seconds": timer_seconds}))
    return jsonify({"status": "success", "seconds": timer_seconds})


@app.route('/timer/configure', methods=['POST'])
def configure_timer():
    global timer_add_seconds
    data = request.get_json()
    with state_lock:
        timer_add_seconds = data.get("add_seconds", 10)
    # Publish to MQTT for BTN configuration
    mqtt_client.publish("Timer Control", json.dumps({"command": "CONFIGURE", "add_seconds": timer_add_seconds}))
    return jsonify({"status": "success", "add_seconds": timer_add_seconds})


@app.route('/timer/stop', methods=['POST'])
def stop_timer():
    global timer_blinking
    with state_lock:
        timer_blinking = False
    mqtt_client.publish("Timer Control", json.dumps({"command": "STOP_BLINK"}))
    return jsonify({"status": "success"})


# ========== RGB ENDPOINTS ==========
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


# ========== PEOPLE COUNT ENDPOINT ==========
@app.route('/people/count', methods=['GET'])
def get_people_count():
    global people_count
    with state_lock:
        return jsonify({"count": people_count})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
