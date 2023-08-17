#!/usr/bin/env python3
from ev3dev2.display import Display
import ev3dev2.fonts as fonts
from ev3dev2.sound import Sound
from datetime import datetime

#region Constants
MIN_LARGE_MOTOR_SPEED = 100 # motor stops if speed is below this
MAX_LARGE_MOTOR_SPEED = 1050
PUSHER_MOTOR_SPEED = 1560
OPENER_MOTOR_OPENING_SPEED = 1560
OPENER_MOTOR_CLOSING_SPEED = -1560
# font list: https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/display.html#bitmap-fonts
DISPLAY_FONT = fonts.load("charB12")
#endregion

#region Helper functions
display = Display()
spkr = Sound()
def speak(text):
    spkr.speak(text, volume = 100, play_type = 1)

def display_info(message: str, do_you_want_to_speak_it = False):
    if (do_you_want_to_speak_it == True):
        speak(message)

    now = datetime.now().strftime("%H:%M:%S")

    print(str.format("[{}] {}", now, message))

    display.text_pixels(
        text = str.format("[{}] {}", now, message),
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

from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
import ev3dev2 as ev3dev2

display_info("Modules loaded.")

#region Initialisation
display_info("Finding PS4 controller...")
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
gamepad = devices[0]
if gamepad.name != "Wireless Controller":
    raise ConnectionError(str.format("PS4 controller not found (found `{}` instead).", gamepad))
display_info("PS4 controller found.")

display_info("Initialising MotorThread.")
class MotorThread(threading.Thread):
    running = True
    forward_speed = 0.0
    side_speed = 0.0
    opener_motor_speed = 0.0
    pusher_motor_running = False

    def __init__(self):
        self.left_motor = LargeMotor(OUTPUT_B)
        self.right_motor = LargeMotor(OUTPUT_C)

        try:
            self.push_motor = LargeMotor(OUTPUT_A)
        except(ev3dev2.DeviceNotFound):
            display_info("No large motor found at Port A (push motor). Proceeding without.")
            pass

        try:
            self.open_motor = MediumMotor(OUTPUT_D)
        except(ev3dev2.DeviceNotFound):
            display_info("No medium motor found at Port D (open motor). Proceeding without.")
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
                self.open_motor.run_forever(
                    speed_sp = self.opener_motor_speed
                )
                if self.pusher_motor_running == True:
                    self.push_motor.run_forever(
                        speed_sp = PUSHER_MOTOR_SPEED
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
            mt.opener_motor_speed = OPENER_MOTOR_CLOSING_SPEED
        elif event.code == 311 and event.value == 1: # R1
            mt.opener_motor_speed = OPENER_MOTOR_OPENING_SPEED
        else:
            mt.opener_motor_speed = 0

        if event.code == 312 and event.value == 1: # L2
            mt.pusher_motor_running = True
        else:
            mt.pusher_motor_running = False

# MQTT
import paho.mqtt.client as paho

MQTT_USERNAME = "ev3maker"
MQTT_PASSWORD = "Test123-"
MQTT_BROKER_ADDRESS = "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud"
MQTT_BROKER_PORT = 8883

MQTT_TOPIC = "ev3/test"

# CONNACK response from server
def on_connect(client, userdata, flags, rc):
    display_info(str.format("Connected to server with result code {}.", rc))

# PUBLISH message from server
def on_message(client, userdata, msg):
    display_info(str.format("{} {}", msg.topic, msg.payload))

client = paho.Client()

client.on_connect = on_connect
client.on_message = on_message

client.tls_set()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

display_info(str.format("Connecting to server..."))
client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT)

client.loop_forever()