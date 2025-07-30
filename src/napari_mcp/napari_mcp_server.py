# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

# napari_mcp_server.py
"""
MCP server that connects to napari via TCP socket.

This script runs as an agent process launched by Claude Desktop or other MCP clients.
It forwards requests to a live napari GUI session over a socket connection.

Usage:
    python napari_mcp_server.py --help
    python napari_mcp_server.py  # starts server on stdin/stdout
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
        "You control a remote napari GUI through a TCP socket. "
        "Use the screenshot tool to see the current viewport.\n\n"
        "Available tools:\n"
        "• open_file(path) - load image files (TIFF, PNG, ND2, NPZ, etc.)\n"
        "• remove_layer(name_or_index) - remove a layer\n"
        "• toggle_view() - switch between 2D and 3D view\n"
        "• iso_contour(layer_name=None, threshold=None) - enable iso-surface rendering\n"
        "• screenshot() - capture current view as JPG\n"
        "• list_layers() - get info about loaded layers\n"
        "• set_colormap(layer_name, colormap) - change layer colormap\n"
        "• set_opacity(layer_name, opacity) - adjust layer transparency\n"
        "• set_blending(layer_name, blending) - set layer blend mode\n"
        "• set_contrast_limits(layer_name, min, max) - adjust contrast\n"
        "• auto_contrast(layer_name) - auto-adjust contrast\n"
        "• set_gamma(layer_name, gamma) - adjust gamma correction\n"
        "• set_interpolation(layer_name, mode) - set interpolation\n"
        "• set_timestep(timestep) - set current time point\n"
        "• get_dims_info() - get dimension info\n"
        "• set_camera(center, zoom, angle) - adjust camera\n"
        "• get_camera() - get camera settings\n"
        "• reset_camera() - reset to default view\n"
        "• add_points(coords, properties, name) - add point annotations\n"
        "• add_shapes(data, shape_type, name) - add shape annotations\n"
        "• add_labels(image, name) - add segmentation masks\n"
        "• add_surface(vertices, faces, name) - add 3D meshes\n"
        "• add_vectors(vectors, name) - add vector fields\n"
        "• save_layers(file_path, layer_names) - save layers to file\n"
        "• export_screenshot(file_path, canvas_only) - save screenshot\n"
        "• get_layer_data(layer_name) - extract layer data\n"
        "• set_scale_bar(visible, unit) - show/hide scale bar\n"
        "• set_axis_labels(labels) - set axis labels\n"
        "• set_view_mode(mode) - change view mode\n"
        "• set_layer_visibility(layer_name, visible) - show/hide layer\n"
        "• measure_distance(point1, point2) - measure between points\n"
        "• get_layer_statistics(layer_name) - get layer stats\n"
        "• crop_layer(layer_name, bounds) - crop layer data\n"
        "• set_channel(index) - set current channel\n"
        "• set_z_slice(index) - set current z-slice\n"
        "• play_animation(start, end, fps) - play time series\n"
    )

    mcp = FastMCP("Napari‑Socket", system_prompt=prompt)

    @mcp.tool()
    def open_file(file_path: str) -> str:  # noqa: WPS430
        """Load an image file into napari."""
        success, message = manager.open_file(file_path)
        return message if success else f"❌ {message}"



    @mcp.tool()
    def remove_layer(name_or_index: str | int) -> str:  # noqa: WPS430
        """Remove a layer by name or index."""
        success, message = manager.remove_layer(name_or_index)
        return message if success else f"❌ {message}"


    @mcp.tool(name="toggle_view")
    def toggle_view() -> str:  # noqa: WPS430
        """Switch between 2D and 3D view."""
        success, message = manager.toggle_ndisplay()
        return message if success else f"❌ {message}"

    @mcp.tool(name="iso_contour")
    def iso_contour(
        layer_name: str | int | None = None,
        threshold: float | None = None,
    ) -> str:  # noqa: WPS430
        """Enable iso-surface rendering for layers."""
        success, message = manager.iso_contour(layer_name, threshold)
        return message if success else f"❌ {message}"

    @mcp.tool(name="screenshot")
    def screenshot() -> str:  # noqa: WPS430
        """Take a screenshot of the current view."""
        success, message = manager.screenshot()
        if success:
            return Image(path=message)  # message is the absolute path to the screenshot
        return f"\u274c {message}"
    
    @mcp.tool(name="list_layers")
    def list_layers() -> str:            # noqa: WPS430
        """Get info about all loaded layers."""
        success, message = manager.list_layers()
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool(name="set_colormap")
    def set_colormap(layer_name: str, colormap: str) -> str:
        """Change the colormap for a layer."""
        success, message = manager.set_colormap(layer_name, colormap)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_opacity(layer_name: str, opacity: float) -> str:
        """Adjust layer transparency (0=transparent, 1=opaque)."""
        success, message = manager.set_opacity(layer_name, opacity)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_blending(layer_name: str, blending: str) -> str:
        """Set how the layer blends with layers below it."""
        success, message = manager.set_blending(layer_name, blending)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_contrast_limits(layer_name: str, contrast_min: float, contrast_max: float) -> str:
        """Set the min/max values for contrast scaling."""
        success, message = manager.set_contrast_limits(layer_name, contrast_min, contrast_max)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def auto_contrast(layer_name: str | None = None) -> str:
        """Automatically adjust contrast to fit the data range."""
        success, message = manager.auto_contrast(layer_name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_gamma(layer_name: str, gamma: float) -> str:
        """Adjust gamma correction for the layer."""
        success, message = manager.set_gamma(layer_name, gamma)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_interpolation(layer_name: str, interpolation: str) -> str:
        """Set the interpolation method for zooming."""
        success, message = manager.set_interpolation(layer_name, interpolation)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_timestep(timestep: int) -> str:
        """Jump to a specific time point."""
        success, message = manager.set_timestep(timestep)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def get_dims_info() -> str:
        """Get info about the viewer's dimensions."""
        success, message = manager.get_dims_info()
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool()
    def set_camera(center=None, zoom=None, angle=None) -> str:
        """Adjust camera position, zoom, and rotation."""
        success, message = manager.set_camera(center, zoom, angle)
        return json.dumps(message) if success else f"❌ {message}"

    @mcp.tool()
    def get_camera() -> str:
        """Get current camera settings."""
        success, message = manager.get_camera()
        return json.dumps(message) if success else f"❌ {message}"

    @mcp.tool()
    def reset_camera() -> str:
        """Reset camera to default view."""
        success, message = manager.reset_camera()
        return json.dumps(message) if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Layer Creation & Annotation Functions
    # ------------------------------------------------------------------
    @mcp.tool()
    def add_points(coordinates: list, properties: dict | None = None, name: str | None = None) -> str:
        """Add point markers to the viewer."""
        success, message = manager.add_points(coordinates, properties, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_shapes(shape_data: list, shape_type: str = 'rectangle', name: str | None = None) -> str:
        """Add shape overlays (rectangles, circles, etc.)."""
        success, message = manager.add_shapes(shape_data, shape_type, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_labels(label_image: list, name: str | None = None) -> str:
        """Add segmentation masks or labeled regions."""
        success, message = manager.add_labels(label_image, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_surface(vertices: list, faces: list, name: str | None = None) -> str:
        """Add 3D mesh surface to the viewer."""
        success, message = manager.add_surface(vertices, faces, name)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def add_vectors(vectors: list, name: str | None = None) -> str:
        """Add vector field arrows to the viewer."""
        success, message = manager.add_vectors(vectors, name)
        return message if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Data Export & Save Functions
    # ------------------------------------------------------------------
    @mcp.tool()
    def save_layers(file_path: str, layer_names: list | None = None) -> str:
        """Save one or more layers to disk."""
        success, message = manager.save_layers(file_path, layer_names)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def export_screenshot(file_path: str, canvas_only: bool = True) -> str:
        """Save a screenshot to a specific location."""
        success, message = manager.export_screenshot(file_path, canvas_only)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def get_layer_data(layer_name: str | int) -> str:
        """Extract the raw data from a layer."""
        success, message = manager.get_layer_data(layer_name)
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Advanced Visualization Controls
    # ------------------------------------------------------------------
    @mcp.tool()
    def set_scale_bar(visible: bool = True, unit: str = 'um') -> str:
        """Show or hide the scale bar."""
        success, message = manager.set_scale_bar(visible, unit)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_axis_labels(labels: list) -> str:
        """Set custom labels for the axes."""
        success, message = manager.set_axis_labels(labels)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_view_mode(mode: str) -> str:
        """Switch between different view modes."""
        success, message = manager.set_view_mode(mode)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_layer_visibility(layer_name: str | int, visible: bool) -> str:
        """Show or hide a specific layer."""
        success, message = manager.set_layer_visibility(layer_name, visible)
        return message if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Measurement & Analysis Functions
    # ------------------------------------------------------------------
    @mcp.tool()
    def measure_distance(point1: list, point2: list) -> str:
        """Calculate distance between two points in the data."""
        success, message = manager.measure_distance(point1, point2)
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool()
    def get_layer_statistics(layer_name: str | int) -> str:
        """Get basic stats (min, max, mean, std) for a layer."""
        success, message = manager.get_layer_statistics(layer_name)
        return json.dumps(message, indent=2) if success else f"❌ {message}"

    @mcp.tool()
    def crop_layer(layer_name: str | int, bounds: list) -> str:
        """Crop a layer to a specific region."""
        success, message = manager.crop_layer(layer_name, bounds)
        return message if success else f"❌ {message}"

    # ------------------------------------------------------------------
    # Time Series & Multi-dimensional Data
    # ------------------------------------------------------------------
    @mcp.tool()
    def set_channel(channel_index: int) -> str:
        """Switch to a specific channel in multi-channel data."""
        success, message = manager.set_channel(channel_index)
        return message if success else f"❌ {message}"

    @mcp.tool()
    def set_z_slice(z_index: int) -> str:
        """Jump to a specific z-slice in 3D data."""
        success, message = manager.set_z_slice(z_index)
        return message if success else f"❌ {message}"

    #TODO currently not working
    @mcp.tool()
    def play_animation(start_frame: int, end_frame: int, fps: int = 10) -> str:
        """Animate through a time series at specified FPS."""
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