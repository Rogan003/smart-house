import time
import random

# Baseline values for stable readings (80% of the time)
baseline_accel = [0.0, 0.0, 1.0]  # Typical at rest (gravity on Z)
baseline_gyro = [0.0, 0.0, 0.0]   # No rotation at rest


def generate_values():
    while True:
        # 15% chance to generate a reading
        if random.randint(0, 100) <= 15:
            # 80% chance: small variations (normal, won't trigger alarm)
            # 20% chance: significant movement (may trigger alarm)
            if random.randint(0, 100) <= 80:
                # Small variations around baseline
                accel = [baseline_accel[i] + random.uniform(-0.3, 0.3) for i in range(3)]
                gyro = [baseline_gyro[i] + random.uniform(-5, 5) for i in range(3)]
            else:
                # Significant movement (20% chance)
                accel = [baseline_accel[i] + random.uniform(-2, 2) for i in range(3)]
                gyro = [baseline_gyro[i] + random.uniform(-100, 100) for i in range(3)]
            yield accel, gyro
        else:
            yield None, None


def run_gyroscope_simulator(delay, callback, stop_event, settings):
    gen = generate_values()
    while not stop_event.is_set():
        time.sleep(delay)
        accel, gyro = next(gen)
        if accel is not None and gyro is not None:
            callback(accel, gyro, settings)
