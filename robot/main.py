#!/usr/bin/env python3
import logging
from threading import Thread
from ev3dev2.led import Leds

logging.basicConfig(format="[%(asctime)s] {%(levelname)s} %(message)s", datefmt="%H:%M:%S", level=logging.DEBUG)

logging.info("ev3.py running.")

LEDs = Leds()

LEDs.set_color("LEFT", "RED")
LEDs.set_color("RIGHT", "RED")

logging.info("Initialising TowerMaintainer and data_sender...")

from TowerMaintainer import TowerMaintainer
from data_sender import start_send_loop


LEDs.set_color("LEFT", "AMBER")
LEDs.set_color("RIGHT", "AMBER")

robot = TowerMaintainer()

controller_read_loop_thread = Thread(target = robot.start_controller_read_loop)
controller_read_loop_thread.start()

# controller_activekeys_loop_thread = Thread(target = robot.start_controller_activekeys_loop)
# controller_activekeys_loop_thread.start()

motors_loop_thread = Thread(target = robot.start_motors_loop)
motors_loop_thread.start()

# COMMENT THESE TWO LINES TO STOP PUBLISHING MESSAGES THROUGH BLUETOOTH SOCKET
send_loop_thread = Thread(target = start_send_loop, args=[robot])
send_loop_thread.start()


LEDs.set_color("LEFT", "GREEN")
LEDs.set_color("RIGHT", "GREEN")