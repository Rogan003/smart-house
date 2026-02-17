import RPi.GPIO as GPIO
import time
from time import sleep
from rgb_controller import rgb_controller

RED_PIN = 12
GREEN_PIN = 13
BLUE_PIN = 19

def run_bedroom_rgb_loop(settings, callback, stop_event):
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

def turnOff():
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.LOW)


def white():
    GPIO.output(RED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    GPIO.output(BLUE_PIN, GPIO.HIGH)


def red():
    GPIO.output(RED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.LOW)


def green():
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    GPIO.output(BLUE_PIN, GPIO.LOW)


def blue():
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.HIGH)


def yellow():
    GPIO.output(RED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    GPIO.output(BLUE_PIN, GPIO.LOW)


def purple():
    GPIO.output(RED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.HIGH)


def lightBlue():
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    GPIO.output(BLUE_PIN, GPIO.HIGH)


if __name__ == "__main__":
    try:
        while True:
            turnOff()
            sleep(1)
            white()
            sleep(1)
            red()
            sleep(1)
            green()
            sleep(1)
            blue()
            sleep(1)
            yellow()
            sleep(1)
            purple()
            sleep(1)
            lightBlue()
            sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
