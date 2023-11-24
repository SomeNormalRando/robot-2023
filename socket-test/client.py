import socket

BLUETOOTH_ADDRESS = "60:f2:62:a9:d8:cc"
CHANNEL = 5

# create a socket object with Bluetooth, TCP & RFCOMM
with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as s:
    s.connect((BLUETOOTH_ADDRESS, CHANNEL))
    # `sendall()` sends all data from bytes, `send()` might not
    s.sendall(b"Hello, world!?!?")
    data = s.recv(1024)

print(data)