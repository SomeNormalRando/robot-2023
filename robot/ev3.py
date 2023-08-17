#!/usr/bin/env python3
from ev3dev2.display import Display
import ev3dev2.fonts as fonts
from ev3dev2.sound import Sound
from datetime import datetime


#region Constants
MIN_LARGE_MOTOR_SPEED = 100 # motor stops if speed is below this
MAX_LARGE_MOTOR_SPEED = 1050
PUSHER_MOTOR_SPEED = 30
PUSHER_MOTOR_ROTATION = 1
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
display_info("Loading modules...", False)

import threading
import evdev
from time import sleep

from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
import ev3dev2
from ev3dev2 import motor
from ev3dev2.power import PowerSupply

import paho.mqtt.client as paho
from paho import mqtt


display_info("Modules loaded.")


class post(threading.Thread):
    def __init__(self):
        self.pow = PowerSupply("/sys/class/power_supply/", "lego-ev3-battery", True)
        self.right_motor = LargeMotor(OUTPUT_C)
        self.left_motor = LargeMotor(OUTPUT_B)
        display_info("MQTT Posting!")
    
        threading.Thread.__init__(self)

    def on_connect(client, userdata, flags, rc, properties=None):
        print("CONNACK received with code %s." % rc)
    
    def on_publish(client, userdata, mid, properties=None):
        print("Published!")
    
    MQTT_USERNAME = "ev3maker"
    MQTT_PASSWORD = "Test123-"
    MQTT_BROKER_ADDRESS = "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud"
    
    def run(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            print("CONNACK received with code %s." % rc)
        def on_publish(client, userdata, mid, properties=None):
            print("Published!")

        MQTT_USERNAME = "ev3maker"
        MQTT_PASSWORD = "Test123-"
        MQTT_BROKER_ADDRESS = "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud"
        
        client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.connect(MQTT_BROKER_ADDRESS, 8883)
        client.on_connect = on_connect
        client.on_publish = on_publish
        client.loop_start()
        while True:
            message = (self.right_motor.speed, self.left_motor.speed, self.pow.measured_volts)
            message = ','.join([str(x) for x in message])
            client.publish("ev3/test", payload=message, qos=1)
            sleep(10)
            

            
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
                    self.push_motor.on_for_rotations(PUSHER_MOTOR_SPEED, PUSHER_MOTOR_ROTATION)
                    self.pusher_motor_running = False
            except motor.SpeedInvalid as e:
                
                pass

mt = MotorThread()
mt.setDaemon(True)
mt.start()

post_thread = post()
post_thread.setDaemon(True)
post_thread.start()

display_info("MotorThread started.")
display_info("Robot fully initialised.", False)
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
        else:
            mt.pusher_motor_running = False
            mt.opener_motor_speed = 0

        
        
        


