#!/usr/bin/env python3
print("ev3.py started")

from ev3dev2.led import Leds
from ev3dev2.sound import Sound
import logging
from datetime import datetime

logging.basicConfig(format="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S", level=logging.DEBUG)

LEDs = Leds()
LEDs.set_color("LEFT", "AMBER")
LEDs.set_color("RIGHT", "AMBER")

#region Constants
MIN_LARGE_MOTOR_SPEED = 100 # motor stops if speed is below this
MAX_LARGE_MOTOR_SPEED = 1050
PUSHER_MOTOR_SPEED = 30
PUSHER_MOTOR_ROTATIONS = 1
# OPENER_MOTOR_OPENING_SPEED = 1560
# OPENER_MOTOR_CLOSING_SPEED = -1560
BRICK_COLOUR_NAMES = ("Red", "Green")
MQTT_USERNAME = "ev3maker"
MQTT_PASSWORD = "Test123-"
MQTT_BROKER_ADDRESS = "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud"
MQTT_BROKER_PORT = 8883
#endregion

#region Helper functions
spkr = Sound()
def speak(text):
    spkr.speak(text, volume = 100, play_type = 1)

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

logging.info("Constants and helper functions loaded.")
logging.info("Loading modules...")

import threading
import evdev
from time import sleep
from json import dumps as stringify_json
from concurrent.futures import ThreadPoolExecutor

from ev3dev2.motor import MediumMotor, LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor import Sensor, INPUT_2, INPUT_4
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.power import PowerSupply

import paho.mqtt.client as paho
from paho import mqtt


logging.info("Modules loaded.")

#region Initialisation
logging.info("Finding PS4 controller...")
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
gamepad = devices[0]
if gamepad.name != "Wireless Controller":
    raise ConnectionError(str.format("PS4 controller not found (found `{}` instead).", gamepad))
logging.info("PS4 controller found.")

class MotorThread(threading.Thread):
    forward_speed = 0.0
    side_speed = 0.0
    # opener_motor_speed = 0.0
    pusher_motor_running = False
    colour_mode = ""
    auto_climbing = False
    publishing = True

    def __init__(self):
        self.power = PowerSupply("/sys/class/power_supply/", "lego-ev3-battery", True)
    
        self.left_motor = LargeMotor(OUTPUT_B)
        self.right_motor = LargeMotor(OUTPUT_C)
    
        self.pusher_motor = LargeMotor(OUTPUT_A)
        # self.opener_motor = MediumMotor(OUTPUT_D)
    
        self.color_sensor = ColorSensor(INPUT_2)
        self.ultrasonic_sensor = Sensor(INPUT_4)
    
        self.init_mqtt()

        threading.Thread.__init__(self)

    def run(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.run_motors)
            executor.submit(self.start_publishing)

    def run_motors(self):
        while True:
            self.left_motor.run_forever(speed_sp = dc_clamp(-self.forward_speed + self.side_speed))
            self.right_motor.run_forever(speed_sp = dc_clamp(self.forward_speed + self.side_speed))
            # # self.opener_motor.run_forever(speed_sp = self.opener_motor_speed)
            if self.pusher_motor_running == True:
                self.pusher_motor.on_for_rotations(PUSHER_MOTOR_SPEED, PUSHER_MOTOR_ROTATIONS)
                self.pusher_motor_running = False

            if mt.auto_climbing == True:
                detected_colour = mt.color_sensor.color_name

                if detected_colour == mt.colour_mode:
                    logging.info(str.format("Colour sensor detected color `{}`. Climbing mode switched to: OFF.", mt.color_sensor.color_name))

                    mt.forward_speed = 0
                    mt.side_speed = 0

                    mt.left_motor.on_for_seconds(speed=MAX_LARGE_MOTOR_SPEED, seconds=7)
                    mt.right_motor.on_for_seconds(speed=MAX_LARGE_MOTOR_SPEED, seconds=7)

                    mt.auto_climbing = False
                    mt.colour_mode = ""

    def init_mqtt(self):
        self.client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        logging.info("[MQTT] Connecting to broker...")
        self.client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT)

        self.client.enable_logger()

        self.client.loop_start()
        logging.info("[MQTT] Network loop started.")

    def start_publishing(self):
        logging.info("start_publishing")
        while True:
            if self.publishing == True:
                message = self.create_message()
                self.client.publish("ev3/test", payload=message, qos=1)
                sleep(1)

    def create_message(self):
        messageDict = {
            # python timestamp is in seconds while JavaScript timestamp is in milliseconds
            "timestamp": int(datetime.timestamp(datetime.now()) * 1000),
            "batteryLevel": self.power.measured_volts,
            "leftMotorSpeed": self.left_motor.speed,
            "rightMotorSpeed": self.right_motor.speed,
            # "openerMotorSpeed": self.opener_motor.speed,
            "pusherMotorSpeed": self.pusher_motor.speed,
            "detectedColour": self.color_sensor.color_name,
            # ultrasonic sensor is installed 5-6 cm above the ground
            "height": self.ultrasonic_sensor.value() - 5,
        }
        return stringify_json(messageDict)

logging.info("Initialising MotorThread class.")
mt = MotorThread()
mt.setDaemon(True)
mt.start()

logging.info("MotorThread started.")
logging.info("Robot fully initialised.")

LEDs.set_color("LEFT", "GREEN")
LEDs.set_color("RIGHT", "GREEN")
#endregion

# loops infinitely
for event in gamepad.read_loop():
    # stop controller from doing anything if robot is in climbing mode
    if mt.auto_climbing == True:
        if event.type == 1 and event.value == 1 and (event.code == 308 or event.code == 305):
            logging.info(str.format("Climbing mode [colour: {}] switched OFF.", mt.colour_mode))

            mt.forward_speed = 0
            mt.side_speed = 0

            mt.auto_climbing = False
            
            mt.colour_mode = ""
        continue

    # left joystick moved
    if event.type == 3:
        if event.code == 0:     # X axis on left stick
            mt.forward_speed = -scale_stick(event.value)
        elif event.code == 1:   # Y axis on left stick
            mt.side_speed = -scale_stick(event.value)

    # buttons pressed
    if event.type == 1 and event.value == 1:
        if event.code == 310:   # L1 - toggle pusher motor
            mt.pusher_motor_running = True

        # elif event.code == 311: # R1: open opener
            # mt.opener_motor_speed = OPENER_MOTOR_OPENING_SPEED
        # elif event.code == 313: # R2: close opener
            # mt.opener_motor_speed = OPENER_MOTOR_CLOSING_SPEED
        # elif event.code == 307: # triangle button: move up
            # mt.forward_speed = 0
            # mt.side_speed = MAX_LARGE_MOTOR_SPEED
        # elif event.code == 304: # X button: move down
        #     mt.forward_speed = 0
        #     mt.side_speed = -MAX_LARGE_MOTOR_SPEED

        elif event.code == 312: # L2: toggle publishing (dev)
            if mt.publishing == True:
                logging.info("[DEV] Stopped publishing.")
                mt.publishing = False
                LEDs.set_color("LEFT", "YELLOW")
                LEDs.set_color("RIGHT", "YELLOW")
            else:
                mt.publishing = True
                logging.info("[DEV] Started publishing again.")
                LEDs.set_color("LEFT", "GREEN")
                LEDs.set_color("RIGHT", "GREEN")
        elif event.code == 308: # square button
            mt.colour_mode = "Red"
            logging.info(str.format("Climbing mode [colour: {}] switched ON.", mt.colour_mode))
            mt.auto_climbing = True

            mt.forward_speed = 0
            mt.side_speed = MAX_LARGE_MOTOR_SPEED

            # mt.opener_motor_speed = 0
            mt.pusher_motor_running = False
        elif event.code == 305: # circle button
            mt.colour_mode = "Green"
            logging.info(str.format("Climbing mode [colour: {}] switched ON.", mt.colour_mode))
            mt.auto_climbing = True

            mt.forward_speed = 0
            mt.side_speed = MAX_LARGE_MOTOR_SPEED

            # mt.opener_motor_speed = 0
            mt.pusher_motor_running = False
        else:
            mt.forward_speed = 0
            mt.side_speed = 0

            # mt.opener_motor_speed = 0
            mt.pusher_motor_running = False