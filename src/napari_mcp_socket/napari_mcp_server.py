
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