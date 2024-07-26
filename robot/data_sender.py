import socket

from time import sleep
from datetime import datetime
import logging
from json import dumps as stringify_json

# from TowerMaintainer import TowerMaintainer

# JC's laptop address: D8:12:65:88:74:74
BLUETOOTH_ADDRESS = "60:f2:62:a9:d8:cc"
CHANNEL = 5

def start_send_loop(robot):
    # create a socket object with Bluetooth, TCP & RFCOMM
    with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as s:
        try:
            s.connect((BLUETOOTH_ADDRESS, CHANNEL))
        except ConnectionError as error:
            logging.error("Connection failed:")
            logging.error(error)
            return

        logging.info(str.format("Successfully connected to server (bluetooth device {}, channel {}).", BLUETOOTH_ADDRESS, CHANNEL))
        robot.connected_to_server = True

        try:
            logging.info("Started Bluetooth socket send loop.")
            while True:
                data_json = stringify_json([
                    # python timestamp is in seconds while JavaScript timestamp is in milliseconds
                    int(datetime.timestamp(datetime.now()) * 1000),
                    robot.power.measured_volts,
                    robot.left_motor.speed,
                    robot.right_motor.speed,
                    robot.pusher_motor.speed
                ])

                # `sendall()` sends all data from bytes, `send()` might not
                s.sendall(data_json.encode())

                logging.debug(str.format("Data sent: {}", data_json))

                sleep(2)
        except ConnectionError as error:
            logging.error("Connection error (robot most likely disconnected from server):")
            logging.error(error)
            robot.connected_to_server = False