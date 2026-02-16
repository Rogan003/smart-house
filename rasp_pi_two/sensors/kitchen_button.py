import RPi.GPIO as GPIO
import time

from colors import print_red


def button_pressed(channel, callback, settings):
    callback(settings)
    print_red("[Kitchen Button] - Clicked")

def run_kitchen_button_loop(settings, callback, stop_event):
    pin = settings['pin']
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(
        pin,
        GPIO.RISING,
        callback=lambda channel: button_pressed(channel, callback, settings),
        bouncetime=100
    )

    if stop_event.is_set():
        GPIO.cleanup()