import RPi.GPIO as GPIO
import time

from colors import print_green


def button_pressed(channel, callback, settings):
    callback(settings)
    print_green("[Door 1] - Door opened")

def run_door_button_one_loop(settings, callback, stop_event):
    pin = settings['pin']
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(
        pin,
        GPIO.RISING,
        callback=lambda channel: button_pressed(channel, callback, settings),
        bouncetime=100
    )

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        GPIO.remove_event_detect(pin)