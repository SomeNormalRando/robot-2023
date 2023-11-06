import socket
from time import sleep
import logging
from json import dumps as stringify_json
from TowerMaintainer import TowerMaintainer

BLUETOOTH_ADDRESS = "60:f2:62:a9:d8:cc"
CHANNEL = 5

def start_send_loop(robot: TowerMaintainer):
    # create a socket object with Bluetooth, TCP & RFCOMM
    with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as s:
        print(s)

        s.connect((BLUETOOTH_ADDRESS, CHANNEL))
        logging.info("Connected to bluetooth device {BLUETOOTH_ADDRESS} at channel {CHANNEL}.")

        logging.info("Starting send loop.")
        while True:
            data = [
                robot.power.measured_volts,
                robot.left_motor.speed,
                robot.right_motor.speed
            ]

            data_json = stringify_json(data)

            # `sendall()` sends all data from bytes, `send()` might not
            s.sendall(data_json.encode())

            logging.debug("Data sent: {data_json}")

            sleep(2)