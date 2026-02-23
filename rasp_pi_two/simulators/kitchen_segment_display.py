import time
from kitchen_timer import kitchen_timer
from colors import Colors, print_blue, print_separator

def print_rainbow(message):
    """Print message with 3 alternating colors"""
    colors = [Colors.RED, Colors.YELLOW, Colors.CYAN]
    result = ""
    for i, char in enumerate(message):
        result += colors[i % len(colors)] + char
    print(result + Colors.RESET)


def run_kitchen_segment_display_simulator(callback, stop_event, settings):
    """
    4SD Display simulator - displays timer value received from server via MQTT.
    Server is the single source of truth for timer countdown.
    PI2's kitchen_timer is updated via MQTT from server.
    """
    show_zero = True
    last_value = None
    blink_announced = False
    
    while not stop_event.is_set():
        time.sleep(0.5)  # Check more frequently for responsive display
        
        if kitchen_timer.is_blinking():
            # When blinking, alternate between 00:00 and blank
            if show_zero:
                current_val = "00:00"
            else:
                current_val = "    "
            show_zero = not show_zero
            
            # Only announce blinking ONCE with rainbow text
            if not blink_announced:
                print()
                print_rainbow("🎉🎉🎉 [4SD] TIMER FINISHED - BLINKING! 🎉🎉🎉")
                print_separator()
                blink_announced = True
            
            # Still update callback for batch publishing, but don't print
            if current_val != last_value:
                callback(settings, current_val, verbose=False)
                last_value = current_val
        else:
            blink_announced = False  # Reset for next time
            
            # Display current timer value (set by server via MQTT)
            timer_val = kitchen_timer.get_time()
            mins = timer_val // 60
            secs = timer_val % 60
            current_val = f"{mins:02d}:{secs:02d}"
            
            # Only publish and print if changed AND last 5 seconds
            if current_val != last_value:
                # Print only in last 5 seconds
                should_print = timer_val <= 5 and timer_val > 0
                callback(settings, current_val, verbose=should_print)
                last_value = current_val
            
            show_zero = True
