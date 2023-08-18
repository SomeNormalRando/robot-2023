#!/usr/bin/env python3
print("ev3.py started")

from ev3dev2.display import Display
import ev3dev2.fonts as fonts
from ev3dev2.led import Leds
from ev3dev2.sound import Sound
from datetime import datetime, timezone, timedelta

LEDs = Leds()
LEDs.set_color("LEFT", "AMBER")
LEDs.set_color("RIGHT", "AMBER")

#region Constants
MIN_LARGE_MOTOR_SPEED = 100 # motor stops if speed is below this
MAX_LARGE_MOTOR_SPEED = 1050
PUSHER_MOTOR_SPEED = 30
PUSHER_MOTOR_ROTATION = 1
OPENER_MOTOR_OPENING_SPEED = 1560
OPENER_MOTOR_CLOSING_SPEED = -1560
# font list: https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/ev3dev-stretch/display.html#bitmap-fonts
DISPLAY_FONT = fonts.load("charB12")
MQTT_USERNAME = "ev3maker"
MQTT_PASSWORD = "Test123-"
MQTT_BROKER_ADDRESS = "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud"
MQTT_BROKER_PORT = 8883
#endregion

#region Helper functions
display = Display()
spkr = Sound()
def speak(text):
    spkr.speak(text, volume = 100, play_type = 1)

def display_info(message: str, do_you_want_to_speak_it = False):
    if (do_you_want_to_speak_it == True):
        speak(message)

    now = datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M:%S")

    print(str.format("[{}] {}", now, message))

    '''
    display.text_pixels(
        text = str.format("[{}] {}", now, message),
        clear_screen = True,
        x = 0, y = 0,
        text_color = "OrangeRed",
        font = DISPLAY_FONT
    )
    display.update()
    '''

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
display_info("Loading modules...", False)

import threading
import evdev
from time import sleep
from json import dumps as stringify_json
from concurrent.futures import ThreadPoolExecutor

from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
import ev3dev2
from ev3dev2 import motor
from ev3dev2.power import PowerSupply

import paho.mqtt.client as paho
from paho import mqtt



display_info("Modules loaded.")

#region Initialisation
display_info("Finding PS4 controller...")
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
gamepad = devices[0]
if gamepad.name != "Wireless Controller":
    raise ConnectionError(str.format("PS4 controller not found (found `{}` instead).", gamepad))
display_info("PS4 controller found.")

class MotorThread(threading.Thread):
    forward_speed = 0.0
    side_speed = 0.0
    opener_motor_speed = 0.0
    pusher_motor_running = False
    publishing = True

    def __init__(self):

        self.power = PowerSupply("/sys/class/power_supply/", "lego-ev3-battery", True)

        self.left_motor = LargeMotor(OUTPUT_B)
        self.right_motor = LargeMotor(OUTPUT_C)

        try:
            self.pusher_motor = LargeMotor(OUTPUT_A)
        except(ev3dev2.DeviceNotFound):
            display_info("No large motor found at Port A (push motor). Proceeding without.")
            pass

        try:
            self.opener_motor = MediumMotor(OUTPUT_D)
        except(ev3dev2.DeviceNotFound):
            display_info("No medium motor found at Port D (open motor). Proceeding without.")
            pass

        self.init_mqtt()

        threading.Thread.__init__(self)

    def run(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.run_motors)
            executor.submit(self.start_publishing)

    def run_motors(self):
        while True:
            self.left_motor.run_forever(
                speed_sp = dc_clamp(-self.forward_speed + self.side_speed)
            )
            self.right_motor.run_forever(
                speed_sp = dc_clamp(self.forward_speed + self.side_speed)
            )
            try:
                self.opener_motor.run_forever(
                    speed_sp = self.opener_motor_speed
                )
                if self.pusher_motor_running == True:
                    self.pusher_motor.on_for_rotations(PUSHER_MOTOR_SPEED, PUSHER_MOTOR_ROTATION)
                    self.pusher_motor_running = False
            except motor.SpeedInvalid as e:
                pass

    def init_mqtt(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            display_info(str.format("[MQTT] CONNACK received with code `{}`.", rc))
        def on_publish(client, userdata, mid):
            display_info(str.format("[MQTT] Message published.", mid))

        self.client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        display_info("[MQTT] Connecting to broker...")
        self.client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT)

        self.client.on_connect = on_connect
        self.client.on_publish = on_publish

        self.client.loop_start()
        display_info("[MQTT] Network loop started.")

    def start_publishing(self):
        while True:
            if self.publishing == True:
                message = self.create_message()
                self.client.publish("ev3/test", payload=message, qos=1)
                sleep(1)
                

    def create_message(self):
        messageDict = {
            "batteryLevel": self.power.measured_volts,
            "leftMotorSpeed": self.left_motor.speed,
            "rightMotorSpeed": self.right_motor.speed,
            "openerMotorSpeed": self.opener_motor.speed,
            "pusherMotorSpeed": self.pusher_motor.speed,
        }
        return stringify_json(messageDict)

display_info("Initialising MotorThread class.")
mt = MotorThread()
mt.setDaemon(True)
mt.start()

display_info("MotorThread started.")
display_info("Robot fully initialised.", False)

LEDs.set_color("LEFT", "GREEN")
LEDs.set_color("RIGHT", "GREEN")
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
        elif event.code == 310 and event.value == 1: #L1
            mt.pusher_motor_running = True
        elif event.code == 307 and event.value == 1:
            mt.forward_speed = 0
            mt.side_speed = MAX_LARGE_MOTOR_SPEED
        elif event.code == 304 and event.value == 1:
            mt.forward_speed = 0
            mt.side_speed = -MAX_LARGE_MOTOR_SPEED
        elif event.code == 305 and event.value == 1:
            if mt.publishing == True:
                mt.publishing = False
                LEDs.set_color("LEFT", "ORANGE")
                LEDs.set_color("RIGHT", "ORANGE")
            else:
                mt.publishing = True
                LEDs.set_color("LEFT", "GREEN")
                LEDs.set_color("RIGHT", "GREEN")
        else:
            mt.pusher_motor_running = False
            mt.opener_motor_speed = 0
            mt.forward_speed = 0
            mt.side_speed = 0

# square 308 circle 305