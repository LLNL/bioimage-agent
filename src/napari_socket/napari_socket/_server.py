#import json, socketserver, threading
#from napari._qt.qt_main_window import Window
# from napari.utils import get_app
import json, socketserver, threading
from qtpy.QtCore import QTimer
from napari._app_model import get_app_model

class _TCPHandler(socketserver.BaseRequestHandler):
    """
    One handler per incoming connection.
    Expects a single JSON line: ["command.id", [arg1, arg2, ...]]
    """
    def handle(self):
        data = self.request.recv(8192).decode().strip()
        try:
            cmd_id, args = json.loads(data)
            # marshal into GUI thread via Qt event-loop
            # get_app().invoke_later(
            #     get_app().commands.execute_command, cmd_id, *(args or [])
            # )
            app = get_app_model()                   # ← new helper
            # Schedule on the GUI thread without blocking this one
            QTimer.singleShot(
                0, lambda: app.commands.execute_command(cmd_id, *(args or []))
            )
            self.request.sendall(b"OK\n")
        except Exception as exc:
            self.request.sendall(f"ERR {exc}\n".encode())


class CommandServer(threading.Thread):
    """
    Runs `socketserver.TCPServer` in its own thread so Qt stays responsive.
    """
    #def __init__(self, host="127.0.0.1", port=0):
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        super().__init__(daemon=True)
        self._srv = socketserver.TCPServer((host, port), _TCPHandler, bind_and_activate=False)
        self._srv.allow_reuse_address = True
        self._srv.server_bind()
        self._srv.server_activate()

    # public -----------------------------------------------------------------
    @property
    def port(self) -> int:
        return self._srv.server_address[1]

    def run(self):
        self._srv.serve_forever()

    def shutdown(self):
        self._srv.shutdown()