import socket, json

HOST, PORT = "127.0.0.1", 53378          # put the port you saw in the widget
cmd = ["napari:toggle_theme", []]        # any valid command id + args

with socket.create_connection((HOST, PORT)) as s:
    s.sendall(json.dumps(cmd).encode() + b"\n")
    print("response:", s.recv(1024).decode().strip())