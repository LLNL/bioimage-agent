"""
Napari MCP Server using FastMCP

This script runs as a standalone process and:
1. Creates or connects to a napari viewer instance
2. Exposes key napari functionality through the MCP protocol
3. Updates visualizations in the napari viewer

Usage:
1. Start this server
2. Configure Claude Desktop to use this script
3. Interact with napari through Claude

Author: Assistant
Date: June 11, 2025
"""
import os
import sys
import logging
import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Image
from napari_manager import NapariManager

# Configure logging
log_dir = Path.home() / "napari_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = log_dir / "napari_mcp_server.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Default prompt that instructs Claude how to interact with napari
default_prompt = """
When using napari through this interface, please follow these guidelines:

1. The napari viewer will be automatically connected when the server starts, so no need to call connect() explicitly.

2. napari is a multi-dimensional image viewer that supports various layer types:
   - Image layers: for 2D/3D/nD image data
   - Labels layers: for segmentation masks
   - Points layers: for point annotations
   - Shapes layers: for geometric shapes (rectangles, polygons, etc.)
   - Surface layers: for 3D mesh data
   - Tracks layers: for tracking data over time
   - Vectors layers: for vector field visualization

3. When loading data, napari supports common image formats (TIFF, PNG, JPG, etc.) and can handle multi-dimensional arrays.

4. Always check what layers are available before performing operations on specific layers.

5. Use screenshots to show the current state of the viewer to the user.
"""

logger = logging.getLogger("napari_mcp")

# Create the napari manager
napari_manager = NapariManager()

# Initialize FastMCP server for Claude Desktop integration with default prompt
mcp = FastMCP("Napari", system_prompt=default_prompt)

# ============================================================================
# MCP Tools for napari
# ============================================================================

@mcp.tool()
def load_data(file_path: str) -> str:
    """
    Load data from a file into napari.
    
    Args:
        file_path: Path to the image file (supports TIFF, PNG, JPG, and other common formats)
    
    Returns:
        Status message
    """
    success, message, _, layer_name = napari_manager.load_data(file_path)
    if success and layer_name:
        return f"{message}. Layer added as '{layer_name}'."
    else:
        return message

@mcp.tool()
def add_new_layer(layer_type: str = "image", name: str = None, 
                  width: int = 512, height: int = 512, depth: int = None) -> str:
    """
    Add a new empty layer to napari.
    
    Args:
        layer_type: Type of layer to add. Options: "image", "labels", "points", "shapes", "surface", "tracks", "vectors"
        name: Optional name for the layer (defaults to "New {layer_type}")
        width: Width of the layer for image/labels types (default: 512)
        height: Height of the layer for image/labels types (default: 512)
        depth: Optional depth for 3D layers (if None, creates 2D layer)
    
    Returns:
        Status message
    """
    # Construct shape based on dimensions
    if depth is not None and depth > 0:
        shape = (depth, height, width)
    else:
        shape = (height, width)
    
    success, message, _, layer_name = napari_manager.add_new_layer(
        layer_type=layer_type, 
        name=name, 
        shape=shape
    )
    
    if success and layer_name:
        return f"{message} named '{layer_name}' with shape {shape}."
    else:
        return message

@mcp.tool()
def get_screenshot() -> dict:
    """
    Capture a screenshot of the current napari viewer and display it in chat.
    
    Returns:
        A dictionary containing the path to the saved screenshot and
        the base64-encoded image data.
    """
    success, message, img_path, img_base64 = napari_manager.get_screenshot()
    
    if not success:
        return {"error": message}
    
    return {"path": img_path, "base64_data": img_base64}

@mcp.tool()
def get_layers() -> str:
    """
    Get a list of all layers currently in the napari viewer.
    
    Returns:
        A formatted list of layers with their properties
    """
    success, message, layers_info = napari_manager.get_layers()
    
    if not success:
        return message
    
    if not layers_info:
        return message
    
    # Format the layers information
    result = f"{message}:\n\n"
    for i, layer in enumerate(layers_info, 1):
        result += f"{i}. {layer['name']} ({layer['type']} layer)\n"
        result += f"   - Visible: {layer['visible']}\n"
        result += f"   - Opacity: {layer['opacity']}\n"
        if 'shape' in layer:
            result += f"   - Shape: {layer['shape']}\n"
        elif 'n_elements' in layer:
            result += f"   - Elements: {layer['n_elements']}\n"
        result += "\n"
    
    return result.strip()

@mcp.tool()
def set_active_layer(layer_name: str) -> str:
    """
    Set the active layer by name.
    
    Args:
        layer_name: Name of the layer to make active
    
    Returns:
        Status message
    """
    success, message = napari_manager.set_active_layer(layer_name)
    return message

@mcp.tool()
def list_commands() -> str:
    """
    List all available commands in this napari MCP server.
    
    Returns:
        List of available commands
    """
    commands = [
        "load_data: Load image data from a file",
        "add_new_layer: Add a new empty layer (image, labels, points, shapes, etc.)",
        "get_screenshot: Capture a screenshot of the viewer and display it in chat",
        "get_layers: List all layers in the viewer with their properties",
        "set_active_layer: Set the active layer by name",
        "list_commands: Show this list of available commands"
    ]
    
    return "Available napari commands:\n\n" + "\n".join(commands)


def main():
    parser = argparse.ArgumentParser(description="Napari MCP Server")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no GUI)")
    
    args = parser.parse_args()
    
    try:
        # Connect to napari (create viewer)
        success, message = napari_manager.connect()
        if not success:
            logger.error(f"Failed to connect to napari: {message}")
            sys.exit(1)
        
        logger.info("Starting Napari MCP Server")
        logger.info(message)
        
        # Run the MCP server
        #mcp.run()
        if napari_manager.viewer:          # keep the foreground bump
            napari_manager.viewer.window.activate()

        # Let FastMCP run in the main thread (non-blocking for Qt)
        mcp.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}")

if __name__ == "__main__":
    main()