#!/usr/bin/python3

# this script will activate the screen with motion detected b
# a PIR attached to GPIO pin 4.
# to adjust the screen timeout first use
# 'xset s 10' where 10 is the number of seconds

import os, subprocess, time

from gpiozero import MotionSensor

pir = MotionSensor(4)
number = 0

while True:
    if pir.motion_detected:
        print(f'Motion Detected {number}')
        subprocess.call('xset dpms force on', shell=True)
        number = number + 1
        time.sleep(2)
