#!/usr/bin/env python3
import MPU6050 
import time
import os

mpu = MPU6050.MPU6050()     #instantiate a MPU6050 class object
accel = [0]*3               #store accelerometer data
gyro = [0]*3                #store gyroscope data
def setup():
    mpu.dmp_initialize()    #initialize MPU6050

def run_gyroscope_loop(delay, callback, stop_event, settings):
    setup()
    while not stop_event.is_set():
        accel = mpu.get_acceleration()      #get accelerometer data
        gyro = mpu.get_rotation()           #get gyroscope data
        accel_scaled = [x / 16384.0 for x in accel]
        gyro_scaled = [x / 131.0 for x in gyro]
        callback(accel_scaled, gyro_scaled, settings)
        time.sleep(delay)

def loop():
    while(True):
        accel = mpu.get_acceleration()      #get accelerometer data
        gyro = mpu.get_rotation()           #get gyroscope data
        os.system('clear')
        print("a/g:%d\t%d\t%d\t%d\t%d\t%d "%(accel[0],accel[1],accel[2],gyro[0],gyro[1],gyro[2]))
        print("a/g:%.2f g\t%.2f g\t%.2f g\t%.2f d/s\t%.2f d/s\t%.2f d/s"%(accel[0]/16384.0,accel[1]/16384.0,
            accel[2]/16384.0,gyro[0]/131.0,gyro[1]/131.0,gyro[2]/131.0))
        time.sleep(0.1)
        
if __name__ == '__main__':     # Program start from here
    print("Program is starting ... ")
    setup()
    try:
        loop()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed,the program will exit.
        pass

