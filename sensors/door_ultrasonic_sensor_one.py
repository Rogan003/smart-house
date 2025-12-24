import time

import RPi.GPIO as GPIO


def get_distance(pin_trig, pin_echo):
    GPIO.output(pin_trig, False)
    time.sleep(0.2)

    GPIO.output(pin_trig, True)
    time.sleep(0.00001)

    GPIO.output(pin_trig, False)
    pulse_start_time = time.time()
    pulse_end_time = time.time()

    max_iter = 100

    iter = 0
    while GPIO.input(pin_echo) == 0:
        if iter > max_iter:
            return None
        pulse_start_time = time.time()
        iter += 1

    iter = 0
    while GPIO.input(pin_echo) == 1:
        if iter > max_iter:
            return None
        pulse_end_time = time.time()
        iter += 1

    pulse_duration = pulse_end_time - pulse_start_time
    distance = (pulse_duration * 34300)/2
    return distance

def run_door_ultrasonic_sensor_one_loop(pin_trig, pin_echo, delay, callback, stop_event):
    GPIO.setup(pin_trig, GPIO.OUT)
    GPIO.setup(pin_echo, GPIO.IN)

    while True:
        distance = get_distance(pin_trig, pin_echo)
        if distance is not None:
            callback(distance)

        if stop_event.is_set():
            GPIO.cleanup()
            break

        time.sleep(delay)