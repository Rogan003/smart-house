import time
import RPi.GPIO as GPIO

def button_pressed(channel, callback):
    callback()
    print("Door Number One - Opened")

def run_door_button_one_loop(pin, callback, stop_event):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(
        pin,
        GPIO.RISING,
        callback=lambda channel: button_pressed(channel, callback),
        bouncetime=100
    )

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    finally:
        GPIO.remove_event_detect(pin)