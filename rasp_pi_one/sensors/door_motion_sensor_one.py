import RPi.GPIO as GPIO
import time


def motion_detected(channel, callback, settings):
    callback(settings, "detected")
    print("[Door 1] - Moving detected")

def no_motion(channel, callback, settings):
    callback(settings, "none")
    print("[Door 1] - Moving stopped")

def run_door_motion_sensor_one_loop(settings, callback, stop_event):
    pin = settings['pin']
    GPIO.setup(pin, GPIO.IN)
    
    GPIO.add_event_detect(
        pin,
        GPIO.RISING,
        callback=lambda channel: motion_detected(channel, callback, settings)
    )

    GPIO.add_event_detect(
        pin,
        GPIO.FALLING,
        callback=lambda channel: no_motion(channel, callback, settings)
    )

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        GPIO.remove_event_detect(pin)