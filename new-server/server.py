import logging

logging.basicConfig(format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S", level=logging.DEBUG)

#region FLASK-SOCKETIO (server -> client)
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

SOCKETIO_EVENT_NAME = "ev3-message"

app = Flask(__name__)
socketio = SocketIO(app)

if __name__ == "__main__":
    socketio.run(app)

@app.route("/")
def html():
    return render_template("index.html")

# import eventlet
# from eventlet import wsgi
# wsgi.server(eventlet.listen(("127.0.0.1", 8000)), app)

#endregion

#region BLUETOOTH SOCKET (EV3 -> server)
import socket

BLUETOOTH_ADDRESS = "60:f2:62:a9:d8:cc" # address of the bluetooth device of this computer (the one you are using right now)
CHANNEL = 5

# create a socket object with Bluetooth, TCP & RFCOMM
with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as server_sock:
    server_sock.bind((BLUETOOTH_ADDRESS, CHANNEL))
    server_sock.listen(1)

    logging.info("[Bluetooth socket] Waiting for connection from EV3...")

    conn, address = server_sock.accept()

    logging.info(f"[Bluetooth socket] {address} connected.")

    while True:
        raw_data = conn.recv(1024)
        if not raw_data:
            break

        data = raw_data.decode()

        logging.info("[Bluetooth socket] Data received: {data}")

        # ~ send data to client through socket.io
        def e():
            socketio.emit(SOCKETIO_EVENT_NAME, raw_data)
#endregion