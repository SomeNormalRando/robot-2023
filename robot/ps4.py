#!/usr/bin/env python3
from ev3dev2.display import Display
import ev3dev2.fonts as fonts
from ev3dev2.sound import Sound

#region Constants
MEDIUM_MOTOR_OPENING_SPEED = 1560
MEDIUM_MOTOR_CLOSING_SPEED = -500
MIN_LARGE_MOTOR_SPEED = 100 # motor stops if speed is below this
MAX_LARGE_MOTOR_SPEED = 1050
# font list: https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/display.html#bitmap-fonts
DISPLAY_FONT = fonts.load("charB08")
#endregion

#region Helper functions
display = Display()
spkr = Sound()
def speak(text):
    spkr.speak(text, volume = 100, play_type = 1)

def display_info(message: str, do_you_want_to_speak_it = False):
    print("[INFO] " + message)

    if (do_you_want_to_speak_it == True):
        speak(message)

    display.text_pixels(
        text = "[INFO] " + message,
        clear_screen = True,
        x = 0, y = 0,
        text_color = "OrangeRed",
        font = DISPLAY_FONT
    )
    display.update()

def clamp(num: float, numMin: float, numMax: float):
    return max(min(numMax, num), numMin)

def scale(val: float, src: tuple, dst: tuple):
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value: float):
    return scale(value, (0, 255), (-MAX_LARGE_MOTOR_SPEED, MAX_LARGE_MOTOR_SPEED))
def dc_clamp(value: float):
    # set speed to 0 if it is below minimum
    if value > -MIN_LARGE_MOTOR_SPEED and value < MIN_LARGE_MOTOR_SPEED:
        return 0
    return clamp(value, -MAX_LARGE_MOTOR_SPEED, MAX_LARGE_MOTOR_SPEED)
#endregion

display_info("Constants and helper functions loaded.")
display_info("Loading modules...", True)

import threading
import evdev

from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
import ev3dev2 as ev3dev2
from sound import amogus

display_info("Modules loaded.")

#region Initialisation
display_info("Finding PS4 controller...")
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
gamepad = devices[0]
display_info("PS4 controller found.")

display_info("Initialising MotorThread.")
class MotorThread(threading.Thread):
    running = True
    forward_speed = 0.0
    side_speed = 0.0
    medium_motor_speed = 0.0

    def __init__(self):
        self.left_motor = LargeMotor(OUTPUT_B)
        self.right_motor = LargeMotor(OUTPUT_C)
        try:
            self.medium_motor = MediumMotor(OUTPUT_A)
        except(ev3dev2.DeviceNotFound):
            display_info("No medium motor found at Port A. Proceeding without.")
            pass

        threading.Thread.__init__(self)

    def run(self):
        while True:
            self.left_motor.run_forever(
                speed_sp = dc_clamp(-self.forward_speed + self.side_speed)
            )
            self.right_motor.run_forever(
                speed_sp = dc_clamp(self.forward_speed + self.side_speed)
            )
            try:
                self.medium_motor.run_forever(
                    speed_sp = self.medium_motor_speed
                )
            except:
                pass

mt = MotorThread()
mt.setDaemon(True)
mt.start()

display_info("MotorThread started.")
display_info("Robot fully initialised.", True)
#endregion

for event in gamepad.read_loop():   # this loops infinitely
    if event.type == 3:             # A stick moved
        if event.code == 0:         # X axis on left stick
            mt.forward_speed = -scale_stick(event.value)
        elif event.code == 1:       # Y axis on left stick
            mt.side_speed = -scale_stick(event.value)
    if event.type == 1:
        if event.code == 313 and event.value == 1: # R2
            mt.medium_motor_speed = MEDIUM_MOTOR_OPENING_SPEED
        elif event.code == 311 and event.value == 1: # R1
            mt.medium_motor_speed = MEDIUM_MOTOR_CLOSING_SPEED
        else:
            mt.medium_motor_speed = 0

        if event.code == 312: # L2
            speak("hi guys")
        elif event.code == 310: # L1
            speak("stop trying lee jiya chen")