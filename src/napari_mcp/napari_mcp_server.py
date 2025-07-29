# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

# napari_mcp_server.py
"""
FastMCP wrapper for the socket‑based Napari manager.

Run this script as the *agent* process that Claude Desktop (or another MCP
client) launches.  It forwards requests to the napari GUI over the socket
and relays the response back.

Example::

    $ python napari_mcp_server.py --help
    $ python napari_mcp_server.py  # starts the server on stdin/stdout
"""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import argparse, json, logging, os

from mcp.server.fastmcp import FastMCP, Image

from napari_manager import NapariManager

_LOGGER = logging.getLogger("napari_mcp_socket")


###########################################################################
# CLI parsing / logging
###########################################################################

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Napari MCP server (socket backend)")
    parser.add_argument("--host", default="127.0.0.1", help="Napari‑socket host [default: %(default)s]")
    parser.add_argument("--port", type=int, default=64908, help="Napari‑socket port [default: %(default)s]")
    parser.add_argument("--timeout", type=float, default=5.0, help="TCP timeout seconds [default: %(default)s]")
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log‑level",
    )
    return parser.parse_args()


def _setup_logging(level: str) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)

    log_dir = Path.home() / "napari_logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "napari_mcp_socket.log"

    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


###########################################################################
# FastMCP definition
###########################################################################

def build_mcp(manager: NapariManager) -> FastMCP:
    prompt = (
        "You are controlling a remote napari GUI through a TCP socket. "
        "You can use the screenshot tool to view the viewport."
        "Tools available:\n"
        "• *open_file(path)* – load data (supports TIFF, PNG, ND2, NPZ, etc.)\n"
        "• *remove_layer(name_or_index)* – remove a layer by name or index\n"
        "• *toggle_view()* – switch between 2-D and 3-D rendering\n\n"
        "• *iso_contour(layer_name=None, threshold=None)* – iso-surface rendering\n\n"
        "• *screenshot(path=None)* – save a JPG snapshot, returns path and base64 data\n\n"
        "• *list_layers()* – get loaded-layer info\n\n"
        "• *set_colormap(layer_name, colormap)* – set a layer's colormap\n\n"
        "• *set_opacity(opacity, layer_name=None)* – set layer opacity (0-1)\n\n"
        "• *set_blending(blending, layer_name=None)* – set layer blending mode\n\n"
        "• *set_contrast_limits(min, max, layer_name=None)* – set layer contrast\n\n"
        "• *auto_contrast(layer_name=None)* – auto-adjust layer contrast\n\n"
        "• *set_gamma(gamma, layer_name=None)* – set layer gamma\n\n"
        "• *set_interpolation(interpolation, layer_name=None)* – set layer interpolation\n\n"
        "• *set_timestep(timestep)* – set the current timestep\n\n"
        "• *get_dims_info()* – get information about the viewer's dimensions\n\n"
        "• *set_camera(center, zoom, angle)* – set camera parameters\n\n"
        "• *get_camera()* – get current camera parameters\n\n"
        "• *reset_camera()* – reset camera to default view\n\n"
        "• *add_points(coordinates, properties=None, name=None)* – add point annotations\n\n"
        "• *add_shapes(shape_data, shape_type='rectangle', name=None)* – add shape annotations\n\n"
        "• *add_labels(label_image, name=None)* – add segmentation masks\n\n"
        "• *add_surface(vertices, faces, name=None)* – add 3D surface meshes\n\n"
        "• *add_vectors(vectors, name=None)* – add vector fields\n\n"
        "• *save_layers(file_path, layer_names=None)* – save layers to file\n\n"
        "• *export_screenshot(file_path, canvas_only=True)* – save screenshot to specific path\n\n"
        "• *get_layer_data(layer_name)* – extract layer data as arrays\n\n"
        "• *set_scale_bar(visible=True, unit='um')* – add/remove scale bar\n\n"
        "• *set_axis_labels(labels)* – set axis labels\n\n"
        "• *set_view_mode(mode)* – set view mode (2D, 3D)\n\n"
        "• *set_layer_visibility(layer_name, visible)* – show/hide layers\n\n"
        "• *measure_distance(point1, point2)* – measure distance between points\n\n"
        "• *get_layer_statistics(layer_name)* – get layer statistics (min, max, mean, std)\n\n"
        "• *crop_layer(layer_name, bounds)* – crop layer to specific bounds\n\n"
        "• *set_channel(channel_index)* – set current channel\n\n"
        "• *set_z_slice(z_index)* – set current z-slice\n\n"
        "• *play_animation(start_frame, end_frame, fps=10)* – animate through time series\n\n"
        "Each call returns 'OK' on success or an 'ERR …' string on failure."
        "If you need to view the viewport, use the screenshot tool."
    )

    mcp = FastMCP("Napari‑Socket", system_prompt=prompt)

    @mcp.tool()
    def open_file(file_path: str) -> str:  # noqa: WPS430
        """Open *file_path* in napari via the socket plugin."""
        success, message = manager.open_file(file_path)
        return message if success else f"❌ {message}"



    @mcp.tool()
    def remove_layer(name_or_index: str | int) -> str:  # noqa: WPS430
        """Remove a layer by its name or positional index."""
        success, message = manager.remove_layer(name_or_index)
        return message if success else f"❌ {message}"


    @mcp.tool(name="toggle_view")
    def toggle_view() -> str:  # noqa: WPS430
        """Toggle between 2-D and 3-D view modes in napari."""
        success, message = manager.toggle_ndisplay()
        return message if success else f"❌ {message}"

    @mcp.tool(name="iso_contour")
    def iso_contour(
        layer_name: str | int | None = None,
        threshold: float | None = None,
    ) -> str:  # noqa: WPS430
        """Switch selected (or all) layers to iso-surface rendering."""
        success, message = manager.iso_contour(layer_name, threshold)
        return message if success else f"❌ {message}"

    @mcp.tool(name="screenshot")
    def screenshot() -> str:  # noqa: WPS430
        """Save a JPG screenshot of the current viewer and return the file path."""
        success, message = manager.screenshot()
        if success:
            return Image(path=message)  # message is the absolute path to the screenshot
        return f"\u274c {message}"
    
    @mcp.tool(name="list_layers")
    def list_layers() -> str:            # noqa: WPS430
        """Return JSON describing every loaded layer."""
        success, message = manager.list_layers()
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool(name="set_colormap")
    def set_colormap(layer_name: str, colormap: str) -> str:
        """Set the colormap for a specific layer."""
        success, message = manager.set_colormap(layer_name, colormap)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_opacity(layer_name: str, opacity: float) -> str:
        """Set the opacity for a given layer (or the active one)."""
        success, message = manager.set_opacity(layer_name, opacity)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_blending(layer_name: str, blending: str) -> str:
        """Set the blending mode for a given layer (or the active one)."""
        success, message = manager.set_blending(layer_name, blending)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_contrast_limits(layer_name: str, contrast_min: float, contrast_max: float) -> str:
        """Set the contrast limits for a given layer (or the active one)."""
        success, message = manager.set_contrast_limits(layer_name, contrast_min, contrast_max)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def auto_contrast(layer_name: str | None = None) -> str:
        """Auto-adjust contrast for a given layer (or the active one)."""
        success, message = manager.auto_contrast(layer_name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_gamma(layer_name: str, gamma: float) -> str:
        """Set the gamma for a given layer (or the active one)."""
        success, message = manager.set_gamma(layer_name, gamma)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_interpolation(layer_name: str, interpolation: str) -> str:
        """Set the interpolation for a given layer (or the active one)."""
        success, message = manager.set_interpolation(layer_name, interpolation)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_timestep(timestep: int) -> str:
        """Set the current timestep."""
        success, message = manager.set_timestep(timestep)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def get_dims_info() -> str:
        """Get information about the viewer's dimensions."""
        success, message = manager.get_dims_info()
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool()
    def set_camera(center=None, zoom=None, angle=None) -> str:
        """Set the camera parameters: center (tuple), zoom (float), angle (tuple for 3D)."""
        success, message = manager.set_camera(center, zoom, angle)
        return json.dumps(message) if success else f"❌ {message}"

    @mcp.tool()
    def get_camera() -> str:
        """Get the current camera parameters."""
        success, message = manager.get_camera()
        return json.dumps(message) if success else f"❌ {message}"

    @mcp.tool()
    def reset_camera() -> str:
        """Reset the camera to the default view."""
        success, message = manager.reset_camera()
        return json.dumps(message) if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Layer Creation & Annotation Functions
    # ------------------------------------------------------------------
    @mcp.tool()
    def add_points(coordinates: list, properties: dict | None = None, name: str | None = None) -> str:
        """Add point annotations to the viewer."""
        success, message = manager.add_points(coordinates, properties, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_shapes(shape_data: list, shape_type: str = 'rectangle', name: str | None = None) -> str:
        """Add shape annotations to the viewer."""
        success, message = manager.add_shapes(shape_data, shape_type, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_labels(label_image: list, name: str | None = None) -> str:
        """Add label image (segmentation mask) to the viewer."""
        success, message = manager.add_labels(label_image, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_surface(vertices: list, faces: list, name: str | None = None) -> str:
        """Add 3D surface mesh to the viewer."""
        success, message = manager.add_surface(vertices, faces, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_vectors(vectors: list, name: str | None = None) -> str:
        """Add vector field to the viewer."""
        success, message = manager.add_vectors(vectors, name)
        return message if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Data Export & Save Functions
    # ------------------------------------------------------------------
    @mcp.tool()
    def save_layers(file_path: str, layer_names: list | None = None) -> str:
        """Save layers to file."""
        success, message = manager.save_layers(file_path, layer_names)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def export_screenshot(file_path: str, canvas_only: bool = True) -> str:
        """Export screenshot to specific file path."""
        success, message = manager.export_screenshot(file_path, canvas_only)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def get_layer_data(layer_name: str | int) -> str:
        """Extract layer data as numpy array."""
        success, message = manager.get_layer_data(layer_name)
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Advanced Visualization Controls
    # ------------------------------------------------------------------
    @mcp.tool()
    def set_scale_bar(visible: bool = True, unit: str = 'um') -> str:
        """Add or remove scale bar."""
        success, message = manager.set_scale_bar(visible, unit)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_axis_labels(labels: list) -> str:
        """Set axis labels."""
        success, message = manager.set_axis_labels(labels)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_view_mode(mode: str) -> str:
        """Set view mode (2D, 3D, etc.)."""
        success, message = manager.set_view_mode(mode)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_layer_visibility(layer_name: str | int, visible: bool) -> str:
        """Set layer visibility."""
        success, message = manager.set_layer_visibility(layer_name, visible)
        return message if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Measurement & Analysis Functions
    # ------------------------------------------------------------------
    @mcp.tool()
    def measure_distance(point1: list, point2: list) -> str:
        """Measure distance between two points."""
        success, message = manager.measure_distance(point1, point2)
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool()
    def get_layer_statistics(layer_name: str | int) -> str:
        """Get statistics for a layer."""
        success, message = manager.get_layer_statistics(layer_name)
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool()
    def crop_layer(layer_name: str | int, bounds: list) -> str:
        """Crop layer to specific bounds."""
        success, message = manager.crop_layer(layer_name, bounds)
        return message if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Time Series & Multi-dimensional Data
    # ------------------------------------------------------------------
    @mcp.tool()
    def set_channel(channel_index: int) -> str:
        """Set current channel."""
        success, message = manager.set_channel(channel_index)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_z_slice(z_index: int) -> str:
        """Set current z-slice."""
        success, message = manager.set_z_slice(z_index)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def play_animation(start_frame: int, end_frame: int, fps: int = 10) -> str:
        """Play animation through time series."""
        success, message = manager.play_animation(start_frame, end_frame, fps)
        return message if success else f"❌ {message}"

    return mcp

    

###########################################################################
# entry‑point
###########################################################################

def main() -> None:  # pragma: no cover
    args = _parse_args()
    _setup_logging(args.loglevel)

    mgr = NapariManager(host=args.host, port=args.port, timeout=args.timeout)
    mcp = build_mcp(mgr)

    _LOGGER.info("Napari MCP (socket backend) listening…")
    mcp.run()


if __name__ == "__main__":
    main()