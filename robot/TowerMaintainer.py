import logging

logging.info("Loading modules...")

import evdev # type: ignore
from PS4Keymap import PS4Keymap
# from datetime import datetime
from time import sleep

from ev3dev2.motor import MoveJoystick, LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2 import DeviceNotFound
from ev3dev2.power import PowerSupply
# from ev3dev2.sensor import Sensor, INPUT_1, INPUT_4
# from ev3dev2.sensor.lego import ColorSensor

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
    PUSHER_MOTOR_SPEED_PERCENT = 30
    OPENER_MOTOR_SPEED = 1560

    def __init__(self):
        self.controller = TowerMaintainer.find_ps4_controller()

        self.connect_inputs_and_outputs()

        self.joystick_x = 0.0
        self.joystick_y = 0.0

        # 0 = idle (not running), 1 = + direction, 2 = - direction
        self.opener_motor_current_speed = 0

        self.power = PowerSupply("/sys/class/power_supply/", "lego-ev3-battery", True)

        # self.currently_publishing = True

    def connect_inputs_and_outputs(self):
        while True:
            try:
                self.move_joystick = MoveJoystick(OUTPUT_B, OUTPUT_C)

                self.pusher_motor = LargeMotor(OUTPUT_A)
                self.left_motor = LargeMotor(OUTPUT_B)
                self.right_motor = LargeMotor(OUTPUT_C)

                # self.ultrasonic_sensor = Sensor(INPUT_1)
                # self.color_sensor = ColorSensor(INPUT_4)

                # this break statement will only be reached if the above code executes without error
                break

            except DeviceNotFound as error:
                logging.error(error)
                logging.info("Initialising again in 3 seconds.")
                sleep(3)

    def start_controller_read_loop(self):
        logging.info("Started PS4 controller read loop.")
        for event in self.controller.read_loop():
            # joystick [do not remove this condition]
            if event.type == 3:
                raw_val = event.value
                if event.code == PS4Keymap.AXE_LX.value: # left joystick, X axis
                    self.joystick_x = TowerMaintainer.scale_joystick(raw_val)
                elif event.code == PS4Keymap.AXE_LY.value: # left joystick, Y axis
                    # "-" in front is to reverse the sign (+/-) of y (the y-axis of the PS4 joystick is reversed - see notes.md)
                    self.joystick_y = -(TowerMaintainer.scale_joystick(raw_val))
            # buttons
            elif event.type == 1:
                if event.code == PS4Keymap.BTN_L1.value:
                    self.pusher_motor.on_for_rotations(TowerMaintainer.PUSHER_MOTOR_SPEED_PERCENT, 1)
    
    """
    def start_controller_activekeys_loop(self):
        while True:
            if PS4Keymap.BTN_R2.value in self.controller.active_keys():
                self.opener_motor_current_speed = TowerMaintainer.OPENER_MOTOR_SPEED
            elif PS4Keymap.BTN_R1.value in self.controller.active_keys():
                self.opener_motor_current_speed = -TowerMaintainer.OPENER_MOTOR_SPEED
            else:
                self.opener_motor_current_speed = 0

            self.opener_motor.run_forever(speed_sp=self.opener_motor_current_speed)
    """

    def start_motors_loop(self):
        logging.info("Started motors loop.")
        while True:
            self.move_joystick.on(
                self.joystick_x if abs(self.joystick_x) > TowerMaintainer.JOYSTICK_THRESHOLD else 0,
                self.joystick_y if abs(self.joystick_y) > TowerMaintainer.JOYSTICK_THRESHOLD else 0,
                TowerMaintainer.JOYSTICK_SCALE_RADIUS
            )