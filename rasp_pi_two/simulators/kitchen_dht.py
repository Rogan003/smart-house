import time
import random


def generate_values(initial_temp=25, initial_humidity=50):
    temperature = initial_temp
    humidity = initial_humidity
    while True:
        # Small variations to simulate stable environment
        temperature = temperature + random.uniform(-0.5, 0.5)
        humidity = humidity + random.uniform(-1, 1)
        
        # Keep within reasonable bounds
        temperature = max(15, min(35, temperature))
        humidity = max(20, min(80, humidity))
        
        yield round(humidity, 1), round(temperature, 1)


def run_dht_simulator(delay, callback, stop_event, publish_event, settings):
    gen = generate_values()
    while not stop_event.is_set():
        time.sleep(delay)
        
        # 15% chance to output a reading
        if random.randint(0, 100) <= 15:
            h, t = next(gen)
            callback(h, t, publish_event, settings)
