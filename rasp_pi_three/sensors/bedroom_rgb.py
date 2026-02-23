import RPi.GPIO as GPIO
import time
from rgb_controller import rgb_controller

def run_bedroom_rgb_loop(settings, callback, stop_event):
    RED_PIN = settings["red_pin"]
    GREEN_PIN = settings["green_pin"]
    BLUE_PIN = settings["blue_pin"]

    GPIO.setup(RED_PIN, GPIO.OUT)
    GPIO.setup(GREEN_PIN, GPIO.OUT)
    GPIO.setup(BLUE_PIN, GPIO.OUT)

    def set_color(color):
        if color == "red":
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)
        elif color == "green":
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.LOW)
        elif color == "blue":
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
        elif color == "white":
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
        elif color == "yellow":
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.LOW)
        elif color == "purple":
            GPIO.output(RED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
        elif color == "lightBlue":
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.HIGH)
            GPIO.output(BLUE_PIN, GPIO.HIGH)
        elif color == "off":
            GPIO.output(RED_PIN, GPIO.LOW)
            GPIO.output(GREEN_PIN, GPIO.LOW)
            GPIO.output(BLUE_PIN, GPIO.LOW)
        
        callback(color, settings)

    # Initial state
    set_color(rgb_controller.get_color())
    
    # Register callback in controller to react immediately
    rgb_controller.set_callback(set_color)

    while not stop_event.is_set():
        time.sleep(0.1)
