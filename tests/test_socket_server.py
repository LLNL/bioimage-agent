import json, socket
host, port = "127.0.0.1", 64908   # ← read the port shown by the dock widget

# cmd = ["napari-socket.open_file", [r"D:\Data\Tooth\tooth_103x94x161_uint8.tif"]]

# with socket.create_connection((host, port)) as s:
#     s.sendall((json.dumps(cmd) + "\n").encode())
#     print(s.recv(1024).decode())       # should print “OK”

    # # 1) add an NPZ as an image layer
    # cmd = ["napari-socket.open_npz",
    #        [r"D:\Data\A1_Lattice\npz\strut-0-rotated.npz", "arr_0"]]  # path, array key

    # with socket.create_connection((host, port)) as s:
    #     s.sendall((json.dumps(cmd) + "\n").encode())
    #     print(s.recv(1024).decode())         # → OK

# 2) later on, remove that layer again
cmd = ["napari-socket.remove_layer", ["arr_0"]]
with socket.create_connection((host, port)) as s:
    s.sendall((json.dumps(cmd) + "\n").encode())
    print(s.recv(1024).decode())         # → OK