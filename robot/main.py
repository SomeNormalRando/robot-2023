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

t1 = Thread(target = robot.start_controller_read_loop)
t1.start()

t2 = Thread(target = robot.start_controller_activekeys_loop)
t2.start()

t3 = Thread(target = robot.start_motors_loop)
t3.start()

# COMMENT THESE TWO LINES TO STOP PUBLISHING MESSAGES THROUGH BLUETOOTH SOCKET
t4 = Thread(target = start_send_loop, args=[robot])
t4.start()


logging.info("All initialisation done.")

LEDs.set_color("LEFT", "GREEN")
LEDs.set_color("RIGHT", "GREEN")