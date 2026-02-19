import RPi.GPIO as GPIO
import time
from kitchen_timer import kitchen_timer

def run_kitchen_segment_display_loop(settings, callback, stop_event):
    # GPIO ports for the 7seg pins
    segments = settings['pin']
    # GPIO ports for the digit 0-3 pins
    digits = settings.get('digit_pins', (22, 27, 17, 24))

    for segment in segments:
        GPIO.setup(segment, GPIO.OUT)
        GPIO.output(segment, 0)

    for digit in digits:
        GPIO.setup(digit, GPIO.OUT)
        GPIO.output(digit, 1)

    num = {' ': (0, 0, 0, 0, 0, 0, 0),
           '0': (1, 1, 1, 1, 1, 1, 0),
           '1': (0, 1, 1, 0, 0, 0, 0),
           '2': (1, 1, 0, 1, 1, 0, 1),
           '3': (1, 1, 1, 1, 0, 0, 1),
           '4': (0, 1, 1, 0, 0, 1, 1),
           '5': (1, 0, 1, 1, 0, 1, 1),
           '6': (1, 0, 1, 1, 1, 1, 1),
           '7': (1, 1, 1, 0, 0, 0, 0),
           '8': (1, 1, 1, 1, 1, 1, 1),
           '9': (1, 1, 1, 1, 0, 1, 1)}

    last_decrement_time = time.time()

    while not stop_event.is_set():
        current_time = time.time()
        if kitchen_timer.is_blinking():
            if int(current_time * 2) % 2 == 0: # Blinking every 500ms
                timer_val = "0000"
            else:
                timer_val = "    "
        elif current_time - last_decrement_time >= 1:
            timer_val = kitchen_timer.decrement()
            callback(settings, timer_val)
            last_decrement_time = current_time
        else:
            timer_val = kitchen_timer.get_time()

        s = str(timer_val).rjust(4)
        for digit in range(4):
            for loop in range(0, 7):
                GPIO.output(segments[loop], num[s[digit]][loop])
            
            # The 8th segment is the dot
            if (int(time.time()) % 2 == 0) and (digit == 1):
                GPIO.output(segments[7], 1)
            else:
                GPIO.output(segments[7], 0)

            GPIO.output(digits[digit], 0)
            time.sleep(0.001)
            GPIO.output(digits[digit], 1)