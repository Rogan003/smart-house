import RPi.GPIO as GPIO
import time


def read_line(line, characters, col_pins, callback):
    GPIO.output(line, GPIO.HIGH)

    if GPIO.input(col_pins[0]) == 1:
        callback(characters[0])
    if GPIO.input(col_pins[1]) == 1:
        callback(characters[1])
    if GPIO.input(col_pins[2]) == 1:
        callback(characters[2])
    if GPIO.input(col_pins[3]) == 1:
        callback(characters[3])

    GPIO.output(line, GPIO.LOW)

def run_door_membrane_switch_loop(settings, callback, stop_event):
    pins = settings['pins']

    r1, r2, r3, r4 = pins[0], pins[1], pins[2], pins[3]
    c1, c2, c3, c4 = pins[4], pins[5], pins[6], pins[7]
    col_pins = [c1, c2, c3, c4]

    GPIO.setup(r1, GPIO.OUT)
    GPIO.setup(r2, GPIO.OUT)
    GPIO.setup(r3, GPIO.OUT)
    GPIO.setup(r4, GPIO.OUT)

    GPIO.setup(c1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(c2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(c3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(c4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    try:
        while True:
            read_line(r1, ["1", "2", "3", "A"], col_pins, callback)
            read_line(r2, ["4", "5", "6", "B"], col_pins, callback)
            read_line(r3, ["7", "8", "9", "C"], col_pins, callback)
            read_line(r4, ["*", "0", "#", "D"], col_pins, callback)
            time.sleep(0.2)

            if stop_event.is_set():
                GPIO.cleanup()
                break
    finally:
        pass