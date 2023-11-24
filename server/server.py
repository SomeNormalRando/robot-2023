# Imports
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
import socket
from threading import Thread

logging.basicConfig(format="\x1b[32m[%(asctime)s] \x1b[33m{%(levelname)s} \x1b[34m%(message)s\x1b[0m", datefmt="%H:%M:%S", level=logging.DEBUG)

# Constants
SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 8000
SOCKETIO_EVENT_NAME = "ev3-message"

# flask-socketio [server -> client]
flask_app = Flask(__name__)
socketio_app = SocketIO(flask_app)

if __name__ == "__main__":
    socketio_app.run(app=flask_app)

@flask_app.route("/")
def html():
    return render_template("index.html")

# Bluetooth socket [EV3 -> server]
def bluetooth_socket_loop():
    def client_callback():
        logging.debug("{socket.io} Data sent to client.")

    # address of the bluetooth device of this computer (the one you are using right now)
    #jc address: D8:12:65:88:74:74
    BLUETOOTH_ADDRESS = "60:f2:62:a9:d8:cc" 
    CHANNEL = 5 # random number

    while True:
        # create a socket object with Bluetooth, TCP & RFCOMM
        with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as server_sock:
            server_sock.bind((BLUETOOTH_ADDRESS, CHANNEL))
            server_sock.listen(1)

            logging.info("{Bluetooth socket} Waiting for connection from EV3...")

            sock, address = server_sock.accept()

            logging.info(f"{{Bluetooth socket}} {address} connected.")

            SocketIO.emit(socketio_app, "ev3-message", "test", callback=client_callback)

            while True:
                raw_data = sock.recv(1024)

                if not raw_data:
                    logging.info(f"{{Bluetooth socket}} Disconnected from {address}.")
                    break

                data_str = raw_data.decode()

                logging.debug(f"{{Bluetooth socket}} Data received: {data_str}")

                # ~ send data to client through socket.io
                socketio_app.emit(
                    SOCKETIO_EVENT_NAME,
                    { "data_str": data_str },
                    callback=client_callback
                )
        t = input("\nListen for connection again? [y]: ")
        if t != "y":
            break

# WSGI server
# def wsgi_server_loop():
#     logging.info(f"{{flask-socketio}} Server started at {SERVER_ADDRESS}:{SERVER_PORT}.")
#     wsgi.server(eventlet.listen((SERVER_ADDRESS, SERVER_PORT)), flask_app)

#region RUN STUFF
bluetooth_socket_loop_thread = Thread(target=bluetooth_socket_loop)
bluetooth_socket_loop_thread.start()

# wsgi_server_loop_thread = Thread(target=wsgi_server_loop)
# wsgi_server_loop_thread.start()
#endregion