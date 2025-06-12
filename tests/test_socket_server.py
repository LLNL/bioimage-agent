# import socket, json
# from pathlib import Path
# HOST, PORT = "127.0.0.1", 64496          # put the port you saw in the widget
# # cmd = ["napari.window.file.open_files", [["D:/Data/Tooth/tooth_103x94x161_uint8.tif"]]]
# cmd = ["napari:open_sample", ["napari", "cells"]]
# # server expects one newline-terminated JSON line
# msg = json.dumps(cmd).encode() + b"\n"

# with socket.create_connection((HOST, PORT)) as s:
#     s.sendall(msg)
#     print("response:", s.recv(1024).decode().strip())   # → “OK”

"""
toggle_theme.py – tell the napari-socket server to flip dark/light mode
"""
import json, socket

HOST = "127.0.0.1"
PORT = 56368          # ⬅ replace with the port shown in the Socket Server dock

cmd = ["napari:toggle_theme", []]        # ⬅ no arguments needed
msg = json.dumps(cmd).encode() + b"\n"   # server expects one JSON line

with socket.create_connection((HOST, PORT)) as sock:
    sock.sendall(msg)
    print("reply:", sock.recv(1024).decode().strip())