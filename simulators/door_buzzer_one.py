from colors import print_gray


def buzz(callback):
    callback()
    print_gray("Door Buzzer One - Buzzing")

def run_door_buzzer_one_simulator(callback, stop_event):
    while True:
        if input("Enter DB for door buzzer one") == "DB":
            buzz(callback)

        if stop_event.is_set():
            break