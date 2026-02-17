from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json


app = Flask(__name__)


# InfluxDB Configuration
token = "MnETT6nOjyevCYF5obDzluansp1gyd1w9JbFSutVKUIXNtV6S8EaUeE-LBbMQ7pGUzTpJCJTP39jdks5TlyZoQ=="
org = "iot"
url = "http://localhost:8086"
bucket = "iot"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)


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

mqtt_client.on_connect = on_connect
mqtt_client.on_message = lambda client, userdata, msg: save_to_db(json.loads(msg.payload.decode('utf-8')))

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


# Route to store dummy data
@app.route('/store_data', methods=['POST'])
def store_data():
    try:
        data = request.get_json()
        store_data(data)
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


# @app.route('/simple_query', methods=['GET'])
# def retrieve_simple_data():
#     query = f"""from(bucket: "{bucket}")
#     |> range(start: -10m)
#     |> filter(fn: (r) => r._measurement == "Humidity")"""
#     return handle_influx_query(query)
#
#
@app.route('/aggregate_query', methods=['GET'])
def retrieve_aggregate_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r.name == "Door Button 1")"""
    return handle_influx_query(query)


if __name__ == '__main__':
    app.run(debug=True)
