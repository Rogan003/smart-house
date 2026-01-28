import RPi.GPIO as GPIO
import time

from colors import print_yellow


def turn_diode_on(pin):
    print_yellow("[Door 1] - Door Light ON")
    GPIO.output(pin, GPIO.HIGH)

def turn_diode_off(pin):
    print_yellow("[Door 1] - Door Light OFF")
    GPIO.output(pin, GPIO.LOW)

def toggle(pin, callback):
    callback()
    turn_diode_on(pin)
    time.sleep(1)
    turn_diode_off(pin)

def run_door_led_light_loop(pin, callback, stop_event):
    GPIO.setup(pin, GPIO.OUT)
    toggle(pin, callback)

    if stop_event.is_set():
        GPIO.cleanup()