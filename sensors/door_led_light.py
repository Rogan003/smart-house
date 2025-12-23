import RPi.GPIO as GPIO

def run_door_led_light_loop(pin, delay, callback, stop_event):
    GPIO.setup(pin, GPIO.OUT)
    pass