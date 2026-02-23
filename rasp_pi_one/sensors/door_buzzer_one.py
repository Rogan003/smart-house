import RPi.GPIO as GPIO
import time
from colors import print_blue
from buzzer_controller import buzzer_controller

def buzz(pin, callback, settings):
    print_blue("[Door 1] - Buzzer Buzzing")
    pitch = 440
    duration = 0.1
    callback(settings)

    period = 1.0 / pitch
    delay = period / 2
    cycles = int(duration * pitch)
    for i in range(cycles):
        GPIO.output(pin, True)
        time.sleep(delay)
        GPIO.output(pin, False)
        time.sleep(delay)

def run_door_buzzer_one_loop(settings, callback, stop_event):
    pin = settings['pin']
    GPIO.setup(pin, GPIO.OUT)
    
    while not stop_event.is_set():
        if buzzer_controller.is_active():
            buzz(pin, callback, settings)
            time.sleep(0.3)  # short pause between buzzes
        else:
            time.sleep(0.1)
    
    GPIO.cleanup()