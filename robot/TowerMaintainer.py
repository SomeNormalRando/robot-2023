import logging

logging.info("Loading modules...")

import evdev # type: ignore
from PS4Keymap import PS4Keymap
# from datetime import datetime
from time import sleep

from ev3dev2.motor import MoveJoystick, LargeMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, SpeedPercent
from ev3dev2 import DeviceNotFound
from ev3dev2.power import PowerSupply
from ev3dev2.sensor import Sensor, INPUT_1, INPUT_4
from ev3dev2.sensor.lego import ColorSensor

from typing import Tuple

logging.info("Modules loaded.")

class TowerMaintainer:
    '''
    Receives input from a connected PS4 controller and runs the robot. 
    '''

    #region static methods
    @staticmethod
    def scale_range(val: float, src: Tuple[float, float], dst: Tuple[float, float]):
        MIN = src[0]
        MAX = src[1]
        NEW_MIN = dst[0]
        NEW_MAX = dst[1]
        a = (NEW_MAX - NEW_MIN) / (MAX - MIN)
        b = NEW_MAX - (a * MAX)
        return (a * val) + b

    @staticmethod
    def scale_joystick(val: float):
        return TowerMaintainer.scale_range(
            val,
            (0, 255),
            (-TowerMaintainer.JOYSTICK_SCALE_RADIUS, TowerMaintainer.JOYSTICK_SCALE_RADIUS)
        )
    
    @staticmethod
    def find_ps4_controller():
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        controller = devices[0]
        if controller.name != "Wireless Controller":
            raise ConnectionError(str.format("PS4 controller not found (found `{}` instead).", controller))

        logging.info("PS4 controller found.")

        return controller
    #endregion

    JOYSTICK_SCALE_RADIUS = 100
    JOYSTICK_THRESHOLD = 10
    PUSHER_MOTOR_SPEED_PERCENT = SpeedPercent(30)
    PUSHER_MOTOR_ROTATIONS = 1

    # automatic mode
    _CLIMBING_SPEED_PERCENT_ = 100
    _COLOUR_ = "Red"
    _SECONDS_ = 10

    def __init__(self):
        self.controller = TowerMaintainer.find_ps4_controller()

        self.connect_inputs_and_outputs()

        self.joystick_x = 0.0
        self.joystick_y = 0.0

        self.power = PowerSupply("/sys/class/power_supply/", "lego-ev3-battery", True)

        self.auto_mode = False

        # self.currently_publishing = True

    def connect_inputs_and_outputs(self):
        while True:
            try:
                self.move_joystick = MoveJoystick(OUTPUT_B, OUTPUT_C)

                self.pusher_motor = LargeMotor(OUTPUT_A)
                self.left_motor = LargeMotor(OUTPUT_B)
                self.right_motor = LargeMotor(OUTPUT_C)

                self.colour_sensor = ColorSensor(INPUT_1)
                # self.ultrasonic_sensor = Sensor(INPUT_4)

                # this break statement will only be reached if the above code executes without error
                break

            except DeviceNotFound as error:
                print()
                logging.error(error)
                logging.info("Initialising again in 5 seconds.")
                sleep(5)

    def start_controller_read_loop(self):
        logging.info("Started PS4 controller read loop.")
        for event in self.controller.read_loop():
            # joystick [do not remove this condition]
            if event.type == 3 and self.auto_mode is False:
                raw_val = event.value
                if event.code == PS4Keymap.AXE_LX.value: # left joystick, X axis
                    self.joystick_x = TowerMaintainer.scale_joystick(raw_val)
                elif event.code == PS4Keymap.AXE_LY.value: # left joystick, Y axis
                    # "-" in front is to reverse the sign (+/-) of y (the y-axis of the PS4 joystick is reversed - see notes.md)
                    self.joystick_y = -(TowerMaintainer.scale_joystick(raw_val))

    def start_controller_activekeys_loop(self):
        while True:
            if self.auto_mode is True:
                continue

            active_keys = self.controller.active_keys()

            if PS4Keymap.BTN_L1.value in active_keys:
                    self.pusher_motor.on_for_rotations(TowerMaintainer.PUSHER_MOTOR_SPEED_PERCENT, TowerMaintainer.PUSHER_MOTOR_ROTATIONS)

            if PS4Keymap.BTN_R2.value in active_keys:
                if self.auto_mode is False:
                    self.start_auto_mode()

    def start_motors_loop(self):
        logging.info("Started motors loop.")
        while True:
            self.detected_colour = self.colour_sensor.color_name

            if self.auto_mode is True:
                continue

            self.move_joystick.on(
                self.joystick_x if abs(self.joystick_x) > TowerMaintainer.JOYSTICK_THRESHOLD else 0,
                self.joystick_y if abs(self.joystick_y) > TowerMaintainer.JOYSTICK_THRESHOLD else 0,
                TowerMaintainer.JOYSTICK_SCALE_RADIUS
            )

    def start_auto_mode(self):
        self.auto_mode = True
        logging.info("Automatic mode started. The remote control (PS4 controller) is now DISABLED.")


        while self.detected_colour is not TowerMaintainer._COLOUR_:
            self.move_joystick.on(
                0,
                TowerMaintainer._CLIMBING_SPEED_PERCENT_,
                TowerMaintainer.JOYSTICK_SCALE_RADIUS
            )

        self.move_joystick.off()

        logging.info(str.format("Colour sensor detected colour `{}`. Robot will climb for another {} seconds.", TowerMaintainer._COLOUR_, TowerMaintainer._SECONDS_))
        # sleep(1)

        self.move_joystick.on_for_seconds(
            left_speed = TowerMaintainer._CLIMBING_SPEED_PERCENT_,
            right_speed = TowerMaintainer._CLIMBING_SPEED_PERCENT_,
            seconds = TowerMaintainer._SECONDS_
        )

        logging.info("Pusher motor will activate in 1 second.")
        sleep(1)

        self.pusher_motor.on_for_rotations(TowerMaintainer.PUSHER_MOTOR_SPEED_PERCENT, TowerMaintainer.PUSHER_MOTOR_ROTATIONS)


        self.auto_mode = False
        logging.info("Automatic mode has finished execution. The remote control (PS4 controller) is now ENABLED.\n")
