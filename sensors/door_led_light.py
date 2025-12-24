import RPi.GPIO as GPIO
import time


def toggle(pin, callback):
    callback()
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(pin, GPIO.LOW)

def run_door_led_light_loop(pin, callback, stop_event):
    GPIO.setup(pin, GPIO.OUT)
    toggle(pin, callback)

    if stop_event.is_set():
        GPIO.cleanup()