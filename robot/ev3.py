#!/usr/bin/env python3
print("ev3.py started")

import logging
from ev3dev2.led import Leds

LEDs = Leds()
LEDs.set_color("LEFT", "AMBER")
LEDs.set_color("RIGHT", "AMBER")

logging.basicConfig(format="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S", level=logging.DEBUG)

logging.info("Loading modules...")
import evdev # type: ignore
from keymap import PS4Keymap
from threading import Thread
# from json import dumps as stringify_json
# from datetime import datetime
from time import sleep

from ev3dev2.motor import MoveJoystick, LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2 import DeviceNotFound
# from ev3dev2.power import PowerSupply
# from ev3dev2.sensor import Sensor, INPUT_1, INPUT_4
# from ev3dev2.sensor.lego import ColorSensor

# import paho.mqtt.client as paho
# from ssl import PROTOCOL_TLS

from typing import Tuple

logging.info("Modules loaded.")


class TowerMaintainer:
    '''
    Receives input from a connected PS4 controller and runs the robot. 
    '''

    JOYSTICK_SCALE_RADIUS = 100
    JOYSTICK_THRESHOLD = 5
    PUSHER_MOTOR_SPEED_PERCENT = 30
    OPENER_MOTOR_SPEED = 1000
    opener_motor_speed = 0

    def __init__(self):
        
        self.move_joystick = None
        # self.left_motor = None
        # self.right_motor = None
        self.pusher_motor = None
        self.opener_motor = None

        while True:
            try:
                self.move_joystick = MoveJoystick(OUTPUT_B, OUTPUT_C)

                self.pusher_motor = LargeMotor(OUTPUT_A)
                self.opener_motor = MediumMotor(OUTPUT_D)
                # self.left_motor = LargeMotor(OUTPUT_B)
                # self.right_motor = LargeMotor(OUTPUT_C)

                # self.ultrasonic_sensor = Sensor(INPUT_1)
                # self.color_sensor = ColorSensor(INPUT_4)

                # this break statement will only be reached if the above code executes without error
                break

            except DeviceNotFound as error:
                logging.error(error)
                logging.info("Initialising again in 3 seconds.")
                sleep(3)

        self.controller = self.find_ps4_controller()

        self.joystick_x = 0.0
        self.joystick_y = 0.0

        self.opening = False

        # self.power = PowerSupply("/sys/class/power_supply/", "lego-ev3-battery", True)

        # self.currently_publishing = True

    def start_controller_loop(self):
        logging.info("Started PS4 controller loop.")
        opener_motor_speed = 0
        
        for event in self.controller.read_loop():
            
            if event.type == 3: # joystick [do not remove this condition]
                raw_val = event.value
                if event.code == PS4Keymap.AXE_LX.value: # left joystick, X axis
                    self.joystick_x = TowerMaintainer.scale_joystick(raw_val)
                elif event.code == PS4Keymap.AXE_LY.value: # left joystick, Y axis
                    # "-" in front is to reverse the sign (+/-) of y
                    # (the y-axis of the PS4 joystick is reversed - see notes.md)
                    self.joystick_y = -(TowerMaintainer.scale_joystick(raw_val))

            if event.code == PS4Keymap.BTN_L1.value:
                self.pusher_motor.on_for_rotations(TowerMaintainer.PUSHER_MOTOR_SPEED_PERCENT, 1)

        
            if event.code == PS4Keymap.BTN_R2.value:
                self.opener_motor.run_forever(speed_sp = -self.OPENER_MOTOR_SPEED)
                print("close")
            elif event.code == PS4Keymap.BTN_R1.value:
                self.opener_motor.run_forever(speed_sp = self.OPENER_MOTOR_SPEED)
                print("open")
            else:
                self.opener_motor.run_forever(speed_sp = 0)
                
    def start_motors_loop(self):
        
        logging.info("Started motors loop.")
        while True:
            
            self.move_joystick.on(
                self.joystick_x if abs(self.joystick_x) > TowerMaintainer.JOYSTICK_THRESHOLD else 0,
                self.joystick_y if abs(self.joystick_y) > TowerMaintainer.JOYSTICK_THRESHOLD else 0,
                TowerMaintainer.JOYSTICK_SCALE_RADIUS
            )
            
    

    @staticmethod
    def find_ps4_controller():
        logging.info("Finding PS4 controller...")

        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        controller = devices[0]
        if controller.name != "Wireless Controller":
            raise ConnectionError(str.format("PS4 controller not found (found `{}` instead).", controller))

        logging.info("PS4 controller found.")

        return controller

    @staticmethod
    def scale_range(val: float, src: Tuple[float, float], dst: Tuple[float, float]):
        MIN = src[0]
        MAX = src[1]
        NEW_MIN = dst[0]
        NEW_MAX = dst[1]
        a = (NEW_MAX - NEW_MIN) / (MAX - MIN)
        b = NEW_MAX - (a * MAX)
        # return (a * val) + b
        return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

    @staticmethod
    def scale_joystick(val: float):
        return TowerMaintainer.scale_range(
            val,
            (0, 255),
            (-TowerMaintainer.JOYSTICK_SCALE_RADIUS, TowerMaintainer.JOYSTICK_SCALE_RADIUS)
        )

"""
class MQTTPublisher:
    '''
    Publishes robot data through MQTT.
    '''

    USERNAME = "ev3maker"
    PASSWORD = "Test123-"
    BROKER_ADDRESS = "f67aa56d63fe477796edc000d79019de.s2.eu.hivemq.cloud"
    BROKER_PORT = 8883

    PUBLISH_INTERVAL = 1 # in seconds

    def __init__(self, robot: TowerMaintainer):
        self.client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        self.client.tls_set(tls_version=PROTOCOL_TLS)
        self.client.username_pw_set(MQTTPublisher.USERNAME, MQTTPublisher.PASSWORD)

        logging.info("[MQTT] Connecting to broker...")
        self.client.connect(MQTTPublisher.BROKER_ADDRESS, MQTTPublisher.BROKER_PORT)

        self.client.enable_logger()

        self.client.loop_start()
        logging.info("[MQTT] Network loop started.")


        self.robot = robot

    def create_message(self):
        messageDict = {
            # python timestamp is in seconds while JavaScript timestamp is in milliseconds
            "timestamp": int(datetime.timestamp(datetime.now()) * 1000),
            "batteryLevel": self.robot.power.measured_volts,
            "leftMotorSpeed": self.robot.left_motor.speed,
            "rightMotorSpeed": self.robot.right_motor.speed,
            "pusherMotorSpeed": self.robot.pusher_motor.speed,
            "detectedColour": self.robot.color_sensor.color_name,
            # ultrasonic sensor is installed 5-6 cm above the ground
            "height": self.robot.ultrasonic_sensor.value() - 5,
        }
        return stringify_json(messageDict)

    def start_publish_loop(self):
        logging.info("[MQTT] Started publishing loop.")

        while True:
            if self.robot.currently_publishing == True:
                message = self.create_message()
                self.client.publish("ev3/test", payload=message, qos=1)
                sleep(MQTTPublisher.PUBLISH_INTERVAL)
"""

robot = TowerMaintainer()
# publisher = MQTTPublisher(robot)

t1 = Thread(target = robot.start_controller_loop)
t2 = Thread(target = robot.start_motors_loop)

t1.start()
t2.start()

# executor.submit(publisher.start_publish_loop)