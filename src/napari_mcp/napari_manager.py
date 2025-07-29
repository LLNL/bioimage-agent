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
import numpy as np

_LOGGER = logging.getLogger(__name__)


def _convert_numpy_for_json(obj):
    """Convert numpy arrays to lists for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy_for_json(v) for v in obj]
    else:
        return obj


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
        # Convert numpy arrays to lists for JSON serialization
        payload = _convert_numpy_for_json(payload)
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
    
    def iso_contour_all_layers(self, threshold: float) -> Tuple[bool, str]:
        """Apply iso-surface (contour) rendering to all layers with the given threshold."""
        return self.send_command("napari-socket.iso_contour", [None, threshold])
    

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

    # ------------------------------------------------------------------
    # Layer Creation & Annotation Functions
    # ------------------------------------------------------------------
    def add_points(self, coordinates: list | np.ndarray, properties: dict | None = None, name: str | None = None) -> Tuple[bool, Any]:
        """Add point annotations to the viewer."""
        args = [coordinates]
        if properties is not None:
            args.append(properties)
        if name is not None:
            args.append(name)
        return self.send_command("napari-socket.add_points", args)

    def add_shapes(self, shape_data: list | np.ndarray, shape_type: str = 'rectangle', name: str | None = None) -> Tuple[bool, Any]:
        """Add shape annotations to the viewer."""
        args = [shape_data, shape_type]
        if name is not None:
            args.append(name)
        return self.send_command("napari-socket.add_shapes", args)

    def add_labels(self, label_image: np.ndarray, name: str | None = None) -> Tuple[bool, Any]:
        """Add label image (segmentation mask) to the viewer."""
        args = [label_image]
        if name is not None:
            args.append(name)
        return self.send_command("napari-socket.add_labels", args)

    def add_surface(self, vertices: np.ndarray, faces: np.ndarray, name: str | None = None) -> Tuple[bool, Any]:
        """Add 3D surface mesh to the viewer."""
        args = [vertices, faces]
        if name is not None:
            args.append(name)
        return self.send_command("napari-socket.add_surface", args)

    def add_vectors(self, vectors: np.ndarray, name: str | None = None) -> Tuple[bool, Any]:
        """Add vector field to the viewer."""
        args = [vectors]
        if name is not None:
            args.append(name)
        return self.send_command("napari-socket.add_vectors", args)

    # ------------------------------------------------------------------
    # Data Export & Save Functions
    # ------------------------------------------------------------------
    def save_layers(self, file_path: str, layer_names: list | None = None) -> Tuple[bool, Any]:
        """Save layers to file."""
        args = [file_path]
        if layer_names is not None:
            args.append(layer_names)
        return self.send_command("napari-socket.save_layers", args)

    def export_screenshot(self, file_path: str, canvas_only: bool = True) -> Tuple[bool, Any]:
        """Export screenshot to specific file path."""
        return self.send_command("napari-socket.export_screenshot", [file_path, canvas_only])

    def get_layer_data(self, layer_name: str | int) -> Tuple[bool, Any]:
        """Extract layer data as numpy array."""
        return self.send_command("napari-socket.get_layer_data", [layer_name])

    # ------------------------------------------------------------------
    # Advanced Visualization Controls
    # ------------------------------------------------------------------
    def set_scale_bar(self, visible: bool = True, unit: str = 'um') -> Tuple[bool, Any]:
        """Add or remove scale bar."""
        return self.send_command("napari-socket.set_scale_bar", [visible, unit])

    def set_axis_labels(self, labels: list) -> Tuple[bool, Any]:
        """Set axis labels."""
        return self.send_command("napari-socket.set_axis_labels", [labels])

    def set_view_mode(self, mode: str) -> Tuple[bool, Any]:
        """Set view mode (2D, 3D, etc.)."""
        return self.send_command("napari-socket.set_view_mode", [mode])

    def set_layer_visibility(self, layer_name: str | int, visible: bool) -> Tuple[bool, Any]:
        """Set layer visibility."""
        return self.send_command("napari-socket.set_layer_visibility", [layer_name, visible])

    # ------------------------------------------------------------------
    # Measurement & Analysis Functions
    # ------------------------------------------------------------------
    def measure_distance(self, point1: list, point2: list) -> Tuple[bool, Any]:
        """Measure distance between two points."""
        return self.send_command("napari-socket.measure_distance", [point1, point2])

    def get_layer_statistics(self, layer_name: str | int) -> Tuple[bool, Any]:
        """Get statistics for a layer."""
        return self.send_command("napari-socket.get_layer_statistics", [layer_name])

    def crop_layer(self, layer_name: str | int, bounds: list) -> Tuple[bool, Any]:
        """Crop layer to specific bounds."""
        return self.send_command("napari-socket.crop_layer", [layer_name, bounds])

    # ------------------------------------------------------------------
    # Time Series & Multi-dimensional Data
    # ------------------------------------------------------------------
    def set_channel(self, channel_index: int) -> Tuple[bool, Any]:
        """Set current channel."""
        return self.send_command("napari-socket.set_channel", [channel_index])

    def set_z_slice(self, z_index: int) -> Tuple[bool, Any]:
        """Set current z-slice."""
        return self.send_command("napari-socket.set_z_slice", [z_index])

    def play_animation(self, start_frame: int, end_frame: int, fps: int = 10) -> Tuple[bool, Any]:
        """Play animation through time series."""
        return self.send_command("napari-socket.play_animation", [start_frame, end_frame, fps])

# ---------------------------------------------------------------------------
# quick manual test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mgr = NapariManager()
    ok, msg = mgr.open_file("/path/to/your/image.tif")
    print(ok, msg)

