import time
from dht_storage import dht_storage

def run_living_room_display_simulator(callback, stop_event, settings):
    states = ["DHT1", "DHT2", "Hardcoded"]
    state_index = 0
    last_switch_time = time.time()

    while not stop_event.is_set():
        current_time = time.time()
        if current_time - last_switch_time >= 3:
            state_index = (state_index + 1) % len(states)
            last_switch_time = current_time

        state = states[state_index]
        if state == "DHT1":
            temp, hum = dht_storage.get_dht1()
            line1 = f"DHT1 Temp: {temp}C"
            line2 = f"DHT1 Hum: {hum}%"
        elif state == "DHT2":
            temp, hum = dht_storage.get_dht2()
            line1 = f"DHT2 Temp: {temp}C"
            line2 = f"DHT2 Hum: {hum}%"
        else: # Hardcoded
            line1 = "Temp: 25C"
            line2 = "Hum: 45%"

        callback(line1, line2, settings)
        time.sleep(1)
