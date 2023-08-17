#!/usr/bin/env python3
import evdev
# import ev3dev.auto as ev3
import ev3dev2
from ev3dev2 import motor, display
import threading
import time

#region Helper functions
def display_info(message):
# font list: https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/display.html#bitmap-fonts
    display.Display.text_pixels("INFO:" + message, True, 20, 20, "OrangeRed", ev3dev2.fonts.load("luBSB24"), )

def clamp(num, min, max):
    return max(min(max, num), min)
def scale(val, src, dst):
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value):
    return scale(value, (0, 255), (-1000, 1000))
def dc_clamp(value):
    return clamp(value, -1000,1000)
#endregion

#region Initialisation
print("Finding PS4 controller...")
display_info("Finding PS4 controller...")
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
ps4dev = devices[0].fn

gamepad = evdev.InputDevice(ps4dev)

forward_speed = 0
side_speed = 0
running = True

class MotorThread(threading.Thread):
    def __init__(self):
        self.left_motor = motor.LargeMotor(motor.OUTPUT_B)
        self.right_motor = motor.LargeMotor(motor.OUTPUT_C)
        threading.Thread.__init__(self)

    def run(self):
        print("MotorThread running!")
        display_info("MotorThread running!")
        while running:
            self.right_motor.run_forever(speed_sp = dc_clamp(forward_speed + side_speed))
            self.left_motor.run_forever(speed_sp = dc_clamp(-forward_speed + side_speed))
        self.right_motor.stop()
        self.left_motor.stop()

motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()
#endregion

for event in gamepad.read_loop():   # this loops infinitely
    if event.type == 3:             # A stick is moved
        if event.code == 0:         # X axis on left stick
            forward_speed = -scale_stick(event.value)
        if event.code == 1:         # Y axis on left stick
            side_speed = -scale_stick(event.value)
        if side_speed < 100 and side_speed > -100:
            side_speed = 0
        if forward_speed < 100 and forward_speed > -100:
            forward_speed = 0

    if event.type == 1 and event.code == 305 and event.value == 1:
        print("X button pressed. Stopping.")
        display_info("X button pressed. Stopping.")
        running = False
        time.sleep(0.5) # Wait for the motor thread to finish
        break
