import time

import RPi.GPIO as GPIO

def motion_detected(channel, callback):
    callback()
    print("Door number 1 moving detected")

def no_motion(channel, callback):
    callback()
    print("Door number 1 moving stopped")

def run_door_motion_sensor_one_loop(pin, callback, stop_event):
    GPIO.setup(pin, GPIO.IN)
    GPIO.add_event_detect(pin, GPIO.RISING, callback=motion_detected)
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=no_motion)

    GPIO.add_event_detect(
        pin,
        GPIO.RISING,
        callback=lambda channel: motion_detected(channel, callback)
    )

    GPIO.add_event_detect(
        pin,
        GPIO.FALLING,
        callback=lambda channel: no_motion(channel, callback)
    )

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        GPIO.remove_event_detect(pin)