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



    def remove_layer(self, name_or_index: str | int) -> Tuple[bool, str]:
        """Remove a layer by its name or positional index using the plugin command.

        The command id is *napari‑socket.remove_layer* as declared in the plugin's
        manifest.
        """
        return self.send_command("napari-socket.remove_layer", [name_or_index])


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
    def screenshot(self) -> tuple[bool, str]:
        """Ask the remote viewer to save a JPG screenshot and return the absolute path as a string."""
        return self.send_command("napari-socket.screenshot")

    # ------------------------------------------------------------------
    # layer introspection helper
    # ------------------------------------------------------------------
    def list_layers(self) -> Tuple[bool, Any]:
        """Retrieve metadata for all currently loaded layers."""
        return self.send_command("napari-socket.list_layers")

    def set_colormap(self, layer_name: str | int, colormap: str) -> Tuple[bool, Any]:
        """Set the colormap for a given layer."""
        return self.send_command("napari-socket.set_colormap", [layer_name, colormap])

    def set_opacity(self, layer_name: str | int, opacity: float) -> Tuple[bool, Any]:
        """Set the opacity for a given layer (or the active one)."""
        args = [layer_name, opacity]
        return self.send_command("napari-socket.set_opacity", args)

    def set_blending(self, layer_name: str | int, blending: str) -> Tuple[bool, Any]:
        """Set the blending mode for a given layer (or the active one)."""
        args = [layer_name, blending]
        return self.send_command("napari-socket.set_blending", args)

    def set_contrast_limits(self, layer_name: str | int, contrast_min: float, contrast_max: float) -> Tuple[bool, Any]:
        """Set the contrast limits for a given layer (or the active one)."""
        args = [layer_name, contrast_min, contrast_max]
        return self.send_command("napari-socket.set_contrast_limits", args)

    def auto_contrast(self, layer_name: str | int) -> Tuple[bool, Any]:
        """Auto-adjust contrast for a given layer (or the active one)."""
        args = [layer_name]
        return self.send_command("napari-socket.auto_contrast", args)

    def set_gamma(self, layer_name: str | int, gamma: float) -> Tuple[bool, Any]:
        """Set the gamma for a given layer (or the active one)."""
        args = [layer_name, gamma]
        return self.send_command("napari-socket.set_gamma", args)

    def set_interpolation(self, layer_name: str | int, interpolation: str) -> Tuple[bool, Any]:
        """Set the interpolation for a given layer (or the active one)."""
        args = [layer_name, interpolation]
        return self.send_command("napari-socket.set_interpolation", args)

    def set_timestep(self, timestep: int) -> Tuple[bool, Any]:
        """Set the timestep for the viewer."""
        return self.send_command("napari-socket.set_timestep", [timestep])

    def get_dims_info(self) -> Tuple[bool, Any]:
        """Get information about the viewer's dimensions."""
        return self.send_command("napari-socket.get_dims_info")

    def set_camera(self, center=None, zoom=None, angle=None) -> Tuple[bool, Any]:
        """Set the camera parameters: center (tuple), zoom (float), angle (float or tuple for 3D)."""
        args = []
        if center is not None:
            args.append(center)
        else:
            args.append(None)
        if zoom is not None:
            args.append(zoom)
        else:
            args.append(None)
        if angle is not None:
            args.append(angle)
        else:
            args.append(None)
        return self.send_command("napari-socket.set_camera", args)

    def get_camera(self) -> Tuple[bool, Any]:
        """Get the current camera parameters."""
        return self.send_command("napari-socket.get_camera")

    def reset_camera(self) -> Tuple[bool, Any]:
        """Reset the camera to the default view."""
        return self.send_command("napari-socket.reset_camera")

# ---------------------------------------------------------------------------
# quick manual test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mgr = NapariManager()
    ok, msg = mgr.open_file("/path/to/your/image.tif")
    print(ok, msg)

