import socket

BLUETOOTH_ADDRESS = "60:f2:62:a9:d8:cc"
CHANNEL = 5

# create a socket object with Bluetooth, TCP & RFCOMM
with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as server_sock:
    server_sock.bind((BLUETOOTH_ADDRESS, CHANNEL))
    server_sock.listen(1)

    conn, address = server_sock.accept()

    print(f"{address} connected.")
    while True:
        data = conn.recv(1024)
        if not data:
            break
        print(data)