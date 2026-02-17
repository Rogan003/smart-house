import time
from sensors.lcd.PCF8574 import PCF8574_GPIO
from sensors.lcd.Adafruit_LCD1602 import Adafruit_CharLCD
from dht_storage import dht_storage

def run_living_room_display_loop(settings, callback, stop_event):
    PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
    PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
    try:
        mcp = PCF8574_GPIO(PCF8574_address)
    except:
        try:
            mcp = PCF8574_GPIO(PCF8574A_address)
        except:
            print('I2C Address Error !')
            return

    lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], GPIO=mcp)
    mcp.output(3, 1)     # turn on LCD backlight
    lcd.begin(16, 2)     # set number of LCD lines and columns

    states = ["DHT1", "DHT2", "Hardcoded"]
    state_index = 0
    last_switch_time = time.time()

    while not stop_event.is_set():
        current_time = time.time()
        if current_time - last_switch_time >= 3:
            state_index = (state_index + 1) % len(states)
            last_switch_time = current_time

        state = states[state_index]
        if state == "DHT1":
            temp, hum = dht_storage.get_dht1()
            line1 = f"DHT1 Temp: {temp}C"
            line2 = f"DHT1 Hum: {hum}%"
        elif state == "DHT2":
            temp, hum = dht_storage.get_dht2()
            line1 = f"DHT2 Temp: {temp}C"
            line2 = f"DHT2 Hum: {hum}%"
        else: # Hardcoded
            line1 = "Temp: 25C"
            line2 = "Hum: 45%"

        lcd.setCursor(0, 0)
        lcd.message(line1.ljust(16) + "\n")
        lcd.message(line2.ljust(16))

        callback(line1, line2, settings)
        time.sleep(1)
