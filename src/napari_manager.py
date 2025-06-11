"""
Napari Manager - Encapsulates napari-specific functionality

This class handles the interaction with napari and provides
a clean interface for the MCP server.

Author: Assistant
Date: June 11, 2025
"""
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Any
import tempfile

class NapariManager:
    """
    Encapsulates all napari-specific functionality.
    This class handles the interaction with napari viewer and provides
    a clean interface for the MCP server.
    """

    def __init__(self):
        """Initialize the Napari manager"""
        self.viewer = None
        self.logger = logging.getLogger("napari_manager")
        self._data_folder = ""
        self._screenshot_counter = 0
    
    def connect(self) -> Tuple[bool, str]:
        """
        Create or connect to a napari viewer instance.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            import napari
            
            # Check if a viewer already exists
            if hasattr(napari, '_viewer') and napari._viewer is not None:
                self.viewer = napari._viewer
                self.logger.info("Connected to existing napari viewer")
                return True, "Connected to existing napari viewer"
            else:
                # Create a new viewer
                #self.viewer = napari.Viewer()
                # Create a new viewer and be sure the window is visible
                self.viewer = napari.Viewer()

                # ----- NEW: raise & focus the window -----
                # This tells Qt to put the viewer in the foreground so you see it
                self.viewer.window.activate()
                self.logger.info("Created new napari viewer")
                return True, "Created new napari viewer"
                
        except Exception as e:
            self.logger.error(f"Failed to connect to napari: {str(e)}")
            return False, f"Failed to connect to napari: {str(e)}"

    def load_data(self, file_path: str) -> Tuple[bool, str, Optional[Any], str]:
        """
        Load data from a file into napari.
        
        Args:
            file_path: Path to the data file (supports various image formats)
            
        Returns:
            tuple: (success, message, layer, layer_name)
        """
        try:
            import numpy as np
            from pathlib import Path
            
            if not self.viewer:
                return False, "Error: No viewer connected. Call connect() first.", None, ""
            
            # Record the directory of the loaded file
            self._data_folder = str(Path(file_path).parent)
            file_name = Path(file_path).name
            
            # Try different loading methods based on file extension
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.tif', '.tiff', '.png', '.jpg', '.jpeg', '.bmp']:
                # Load using scikit-image
                try:
                    from skimage import io
                    data = io.imread(file_path)
                    layer = self.viewer.add_image(data, name=file_name)
                    self.logger.info(f"Loaded image data from {file_path}")
                    return True, f"Successfully loaded image from {file_path}", layer, layer.name
                except ImportError:
                    self.logger.warning("scikit-image not available, trying napari's built-in loader")
            
            # Try napari's built-in file opening
            try:
                layers = self.viewer.open(file_path)
                if layers:
                    layer = layers[0] if isinstance(layers, list) else layers
                    return True, f"Successfully loaded data from {file_path}", layer, layer.name
                else:
                    return False, f"Failed to load data from {file_path}", None, ""
            except Exception as open_error:
                self.logger.error(f"Error with napari.open: {str(open_error)}")
                
            # If all methods fail
            return False, f"Could not load file {file_path}. Unsupported format or file not found.", None, ""
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            return False, f"Error loading data: {str(e)}", None, ""
    
    def add_new_layer(self, layer_type: str = "image", name: str = None, 
                      shape: tuple = (512, 512), dtype: str = "uint8") -> Tuple[bool, str, Optional[Any], str]:
        """
        Add a new empty layer to napari.
        
        Args:
            layer_type: Type of layer to add ("image", "labels", "points", "shapes", "surface", "tracks", "vectors")
            name: Optional name for the layer
            shape: Shape of the data for image/labels layers (default: (512, 512))
            dtype: Data type for image/labels layers (default: "uint8")
            
        Returns:
            tuple: (success, message, layer, layer_name)
        """
        try:
            if not self.viewer:
                return False, "Error: No viewer connected. Call connect() first.", None, ""
            
            layer_type = layer_type.lower()
            layer = None
            
            if layer_type == "image":
                # Create empty image data
                data = np.zeros(shape, dtype=dtype)
                layer = self.viewer.add_image(data, name=name or "New Image")
                
            elif layer_type == "labels":
                # Create empty labels data
                data = np.zeros(shape, dtype=np.int32)
                layer = self.viewer.add_labels(data, name=name or "New Labels")
                
            elif layer_type == "points":
                # Create empty points layer
                data = np.empty((0, len(shape)))  # No points initially
                layer = self.viewer.add_points(data, name=name or "New Points")
                
            elif layer_type == "shapes":
                # Create empty shapes layer
                layer = self.viewer.add_shapes(name=name or "New Shapes")
                
            elif layer_type == "surface":
                # Create minimal surface data (single triangle)
                vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
                faces = np.array([[0, 1, 2]], dtype=np.int32)
                values = np.array([0, 0, 0], dtype=np.float32)
                layer = self.viewer.add_surface((vertices, faces, values), name=name or "New Surface")
                
            elif layer_type == "tracks":
                # Create empty tracks layer
                data = np.empty((0, 4))  # tracks need (ID, time, y, x) or (ID, time, z, y, x)
                layer = self.viewer.add_tracks(data, name=name or "New Tracks")
                
            elif layer_type == "vectors":
                # Create empty vectors layer
                # Vectors need shape (N, 2, D) where N is number of vectors, D is dimensionality
                data = np.empty((0, 2, len(shape)))
                layer = self.viewer.add_vectors(data, name=name or "New Vectors")
                
            else:
                return False, f"Unsupported layer type: {layer_type}. Supported types: image, labels, points, shapes, surface, tracks, vectors", None, ""
            
            if layer:
                self.logger.info(f"Added new {layer_type} layer: {layer.name}")
                return True, f"Added new {layer_type} layer", layer, layer.name
            else:
                return False, f"Failed to create {layer_type} layer", None, ""
                
        except Exception as e:
            self.logger.error(f"Error adding new layer: {str(e)}")
            return False, f"Error adding new layer: {str(e)}", None, ""
    
    def get_screenshot(self) -> Tuple[bool, str, Optional[str]]:
        """
        Capture a screenshot from the current viewer.
        
        Returns:
            tuple: (success, message, img_path)
        """
        try:
            if not self.viewer:
                return False, "Error: No viewer connected. Call connect() first.", None
            
            # Create a temporary file for the screenshot
            import tempfile
            import os
            
            # Create temp directory if it doesn't exist
            temp_dir = Path(tempfile.gettempdir()) / "napari_screenshots"
            temp_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            self._screenshot_counter += 1
            screenshot_path = temp_dir / f"napari_screenshot_{self._screenshot_counter}.png"
            
            # Take screenshot using napari's built-in method
            # napari's screenshot method returns an RGBA numpy array
            screenshot_array = self.viewer.screenshot(canvas_only=False)
            
            # Save the screenshot
            from PIL import Image
            img = Image.fromarray(screenshot_array)
            img.save(str(screenshot_path))
            
            self.logger.info(f"Screenshot saved to {screenshot_path}")
            return True, "Screenshot captured", str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {str(e)}")
            return False, f"Error capturing screenshot: {str(e)}", None
    
    def get_layers(self) -> Tuple[bool, str, list]:
        """
        Get a list of all layers in the viewer.
        
        Returns:
            tuple: (success, message, layers_info)
                  layers_info is a list of dicts with layer information
        """
        try:
            if not self.viewer:
                return False, "Error: No viewer connected. Call connect() first.", []
            
            layers_info = []
            for layer in self.viewer.layers:
                layer_info = {
                    'name': layer.name,
                    'type': layer.__class__.__name__.replace('Layer', '').lower(),
                    'visible': layer.visible,
                    'opacity': layer.opacity,
                }
                
                # Add shape info for relevant layer types
                if hasattr(layer, 'data'):
                    if hasattr(layer.data, 'shape'):
                        layer_info['shape'] = layer.data.shape
                    elif isinstance(layer.data, (list, tuple)) and len(layer.data) > 0:
                        # For points, shapes, etc.
                        layer_info['n_elements'] = len(layer.data)
                
                layers_info.append(layer_info)
            
            if not layers_info:
                return True, "No layers in the viewer", []
            
            # Format the message
            message = f"Found {len(layers_info)} layer(s) in the viewer"
            return True, message, layers_info
            
        except Exception as e:
            self.logger.error(f"Error getting layers: {str(e)}")
            return False, f"Error getting layers: {str(e)}", []
    
    def set_active_layer(self, layer_name: str) -> Tuple[bool, str]:
        """
        Set the active layer by name.
        
        Args:
            layer_name: Name of the layer to make active
            
        Returns:
            tuple: (success, message)
        """
        try:
            if not self.viewer:
                return False, "Error: No viewer connected. Call connect() first."
            
            # Find the layer by name
            for layer in self.viewer.layers:
                if layer.name == layer_name:
                    self.viewer.layers.selection.active = layer
                    return True, f"Set active layer to '{layer_name}'"
            
            # Layer not found
            available_layers = [layer.name for layer in self.viewer.layers]
            return False, f"Layer '{layer_name}' not found. Available layers: {', '.join(available_layers)}"
            
        except Exception as e:
            self.logger.error(f"Error setting active layer: {str(e)}")
            return False, f"Error setting active layer: {str(e)}"