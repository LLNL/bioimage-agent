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

from mcp.server.fastmcp import FastMCP

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
        "Tools available:\n"
        "• *open_file(path)* – load data\n"
        "• *toggle_view()* – switch between 2-D and 3-D rendering\n\n"
        "• *iso_contour(layer_name=None, threshold=None)* – iso-surface rendering\n\n"
        "• *screenshot(path=None)* – save a PNG snapshot, returns path and base64 data\n\n"
        "• *list_layers()* – get loaded-layer info\n\n"
        "• *set_colormap(layer_name, colormap)* – set a layer's colormap\n\n"
        "• *set_opacity(opacity, layer_name=None)* – set layer opacity (0-1)\n\n"
        "• *set_blending(blending, layer_name=None)* – set layer blending mode\n\n"
        "• *set_contrast_limits(min, max, layer_name=None)* – set layer contrast\n\n"
        "• *auto_contrast(layer_name=None)* – auto-adjust layer contrast\n\n"
        "• *set_gamma(gamma, layer_name=None)* – set layer gamma\n\n"
        "• *set_interpolation(interpolation, layer_name=None)* – set layer interpolation\n\n"
        "Each call returns 'OK' on success or an 'ERR …' string on failure."
    )

    mcp = FastMCP("Napari‑Socket", system_prompt=prompt)

    @mcp.tool()
    def open_file(file_path: str) -> str:  # noqa: WPS430
        """Open *file_path* in napari via the socket plugin."""
        success, message = manager.open_file(file_path)
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
    def screenshot(path: str | None = None) -> str:  # noqa: WPS430
        """Save a PNG screenshot of the current viewer."""
        success, message = manager.screenshot(path)
        return json.dumps(message) if success else f"❌ {message}"

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