import RPi.GPIO as GPIO
import time


def buzz(pin, callback):
    pitch = 440
    duration = 0.1
    callback()

    period = 1.0 / pitch
    delay = period / 2
    cycles = int(duration * pitch)
    for i in range(cycles):
        GPIO.output(pin, True)
        time.sleep(delay)
        GPIO.output(pin, False)
        time.sleep(delay)

def run_door_buzzer_one_loop(pin, callback, stop_event):
    GPIO.setup(pin, GPIO.OUT)
    buzz(pin, callback)

    if stop_event.is_set():
        GPIO.cleanup()