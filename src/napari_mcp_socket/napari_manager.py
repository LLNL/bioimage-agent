# napari_manager.py
"""
Socket‑based Napari Manager
---------------------------
Encapsulates communication with the *napari‑socket* plugin that runs inside
a live napari GUI session.  All interaction happens over a plain TCP socket
(the plugin listens on 127.0.0.1:64908 by default).

Currently we expose a single helper – ``open_file`` – as proof‑of‑concept.
More commands from the plugin's manifest (``napari.yaml``) can be added by
calling ``NapariManager.send_command`` with the appropriate command id.
"""
from __future__ import annotations

import json
import logging
import pathlib
import socket
from typing import Any, Sequence, Tuple

_LOGGER = logging.getLogger(__name__)


class NapariManager:  # pylint: disable=too-few-public-methods
    """Small helper that talks to the TCP server spawned by *napari‑socket*."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 64908,
        timeout: float = 5.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    # ---------------------------------------------------------------------
    # low‑level I/O helpers
    # ---------------------------------------------------------------------
    def _send(self, payload: dict[str, Any] | list[Any]) -> str:
        """Send *one* JSON payload and return the raw string reply.

        The *napari‑socket* plugin expects **exactly** one JSON line per
        connection and responds with a single line that starts with either
        ``"OK"`` or ``"ERR ..."``.
        """
        data = json.dumps(payload).encode() + b"\n"
        _LOGGER.debug("→ %s", data)

        with socket.create_connection((self.host, self.port), self.timeout) as sck:
            sck.sendall(data)
            reply = sck.recv(8192).decode().strip()

        _LOGGER.debug("← %s", reply)
        return reply

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def send_command(self, cmd_id: str, args: Sequence[Any] | None = None) -> Tuple[bool, Any]:
        """Invoke *cmd_id* inside napari and return *(success, message)*."""
        payload: list[Any] = [cmd_id, list(args or [])]
        reply = self._send(payload)
        if reply == "OK":                 # no payload
            return True, None
        if reply.startswith("OK "):       # payload present
            payload = reply[3:].strip()
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                pass                       # plain-text payload
            return True, payload
        return False, reply

    # ------------------------------------------------------------------
    # high‑level helpers
    # ------------------------------------------------------------------
    def open_file(self, file_path: str | pathlib.Path) -> Tuple[bool, str]:
        """Open *file_path* in napari using the plugin command.

        The command id is *napari‑socket.open_file* as declared in the plugin's
        manifest.
        """
        path = pathlib.Path(file_path).expanduser().resolve()
        if not path.exists():
            return False, f"File not found: {path}"

        return self.send_command("napari-socket.open_file", [str(path)])


    # ------------------------------------------------------------------
    # view helpers
    # ------------------------------------------------------------------
    def toggle_ndisplay(self) -> Tuple[bool, str]:
        """Switch the remote viewer between 2-D and 3-D modes."""
        return self.send_command("napari-socket.toggle_ndisplay")
    
    # ------------------------------------------------------------------
    # iso-surface helper
    # ------------------------------------------------------------------
    def iso_contour(
        self,
        layer_name: str | int | None = None,
        threshold: float | None = None,
    ) -> Tuple[bool, str]:
        """Apply iso-surface (contour) rendering to one or more layers."""
        args: list[Any] = []
        if layer_name is not None:
            args.append(layer_name)
        if threshold is not None:
            args.append(float(threshold))
        return self.send_command("napari-socket.iso_contour", args)
    

    # ------------------------------------------------------------------
    # screenshot helper
    # ------------------------------------------------------------------
    def screenshot(self, path: str | None = None) -> tuple[bool, str]:
        """Ask the remote viewer to save a PNG screenshot."""
        args: list[str] = []
        if path is not None:
            args.append(str(path))
        return self.send_command("napari-socket.screenshot", args)

    # ------------------------------------------------------------------
    # layer introspection helper
    # ------------------------------------------------------------------
    def list_layers(self) -> Tuple[bool, Any]:
        """Retrieve metadata for all currently loaded layers."""
        return self.send_command("napari-socket.list_layers")
# ---------------------------------------------------------------------------
# quick manual test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mgr = NapariManager()
    ok, msg = mgr.open_file("/path/to/your/image.tif")
    print(ok, msg)

