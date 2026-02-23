import time
import random

# Simulate realistic entry/exit patterns
current_distance = 80  # Start at far distance
movement_direction = None  # None, "approaching", or "leaving"
movement_steps = 0


def generate_value(callback, settings):
    global current_distance, movement_direction, movement_steps
    
    # 50% chance to generate a reading (increased frequency)
    if random.randint(0, 100) <= 50:
        # If no active movement, maybe start one
        if movement_direction is None:
            # 40% chance to start a movement sequence (entry or exit)
            if random.randint(0, 100) <= 40:
                movement_direction = random.choice(["approaching", "leaving"])
                movement_steps = random.randint(4, 7)  # 4-7 steps for the movement
                if movement_direction == "approaching":
                    current_distance = random.uniform(70, 90)  # Start far
                else:
                    current_distance = random.uniform(30, 50)  # Start close
        
        # Continue movement sequence
        if movement_direction == "approaching":
            # Distance decreases (person approaching sensor = entering)
            current_distance -= random.uniform(8, 15)
            current_distance = max(20, current_distance)  # Min 20cm
            movement_steps -= 1
        elif movement_direction == "leaving":
            # Distance increases (person moving away = exiting)
            current_distance += random.uniform(8, 15)
            current_distance = min(100, current_distance)  # Max 100cm
            movement_steps -= 1
        
        # End movement if steps done
        if movement_steps <= 0:
            movement_direction = None
        
        callback(round(current_distance, 2), settings)


def run_door_ultrasonic_sensor_two_simulator(delay, callback, stop_event, settings):
    while True:
        time.sleep(delay)
        generate_value(callback, settings)

        if stop_event.is_set():
            break
