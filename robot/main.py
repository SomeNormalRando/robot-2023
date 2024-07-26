#!/usr/bin/env python3
import logging
from threading import Thread    
from ev3dev2.led import Leds

logging.basicConfig(format="\x1b[32m[%(asctime)s] \x1b[33m{%(levelname)s} \x1b[34m%(message)s\x1b[0m", datefmt="%H:%M:%S", level=logging.DEBUG)

logging.info("ev3.py running.")

LEDs = Leds()

LEDs.set_color("LEFT", "RED")
LEDs.set_color("RIGHT", "RED")

logging.info("Initialising TowerMaintainer...")

from TowerMaintainer import TowerMaintainer


LEDs.set_color("LEFT", "AMBER")
LEDs.set_color("RIGHT", "AMBER")

robot = TowerMaintainer()

controller_read_loop_thread = Thread(target = robot.start_controller_read_loop)
controller_read_loop_thread.start()


motors_loop_thread = Thread(target = robot.start_motors_and_activekeys_loop)
motors_loop_thread.start()

# COMMENT THESE TWO LINES TO STOP PUBLISHING MESSAGES THROUGH BLUETOOTH SOCKET
# send_loop_thread = Thread(target = start_send_loop, args=[robot])
# send_loop_thread.start()


LEDs.set_color("LEFT", "GREEN")
LEDs.set_color("RIGHT", "GREEN")