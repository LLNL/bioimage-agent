#!/usr/bin/env python3
"""
Consolidated test suite for NapariManager - combines all test functionality.

This script consolidates the functionality from:
- test_simple.py: Basic connection and dataset loading
- test_connection.py: Connection diagnostics and timeout testing
- test_progressive.py: Progressive step-by-step testing
- test_napari_manager.py: Comprehensive function testing by category

Usage:
    python test_consolidated.py [--timeout TIMEOUT] [--dataset PATH]

Prerequisites:
    - napari-socket plugin must be running in a napari instance
    - napari instance must be listening on the default socket (127.0.0.1:64908)
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
import numpy as np

# Add the src directory to the path
sys.path.append("./src")

from napari_mcp.napari_manager import NapariManager

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Default dataset path
DEFAULT_DATASET_PATH = r"C:\Users\miao1\OneDrive - LLNL\Sharing\multi-channel\SNAP_IgM_BCR_Cell_1\tif\SNAP_IgM_BCR_Cell_1_ch0.tif"

class TestRunner:
    """Consolidated test runner."""
    
    def __init__(self, timeout=30.0, dataset_path=None, keep_test_files=False):
        self.timeout = timeout
        self.dataset_path = dataset_path or DEFAULT_DATASET_PATH
        self.keep_test_files = keep_test_files
        self.mgr = None
        
    def create_manager(self):
        """Create NapariManager instance."""
        logger.info(f"Creating NapariManager with {self.timeout}s timeout...")
        try:
            self.mgr = NapariManager(timeout=self.timeout)
            logger.info("✓ NapariManager created successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create NapariManager: {e}")
            return False
    
    def test_connection_diagnostics(self):
        """Test connection with different timeout values."""
        logger.info("=== Connection Diagnostics ===")
        
        timeouts = [5.0, 10.0, 30.0]
        
        for timeout in timeouts:
            logger.info(f"Testing with timeout: {timeout} seconds")
            
            try:
                mgr = NapariManager(timeout=timeout)
                logger.info(f"✓ NapariManager created with timeout {timeout}s")
                
                start_time = time.time()
                success, result = mgr.list_layers()
                duration = time.time() - start_time
                
                logger.info(f"Command took {duration:.2f} seconds")
                
                if success:
                    logger.info(f"✓ list_layers successful: {len(result) if result else 0} layers")
                    return True
                else:
                    logger.error(f"✗ list_layers failed: {result}")
                    
            except Exception as e:
                logger.error(f"✗ Exception with timeout {timeout}s: {e}")
                if "timed out" in str(e).lower():
                    logger.info(f"  This was a timeout error")
                continue
        
        return False
    
    def test_basic_connection(self):
        """Test basic connection."""
        logger.info("=== Testing Basic Connection ===")
        
        success, result = self.mgr.list_layers()
        if success:
            logger.info(f"✓ Basic connection works: {len(result) if result else 0} layers")
            return True
        else:
            logger.error(f"✗ Basic connection failed: {result}")
            return False
    
    def test_simple_commands(self):
        """Test simple commands that should work quickly."""
        logger.info("=== Testing Simple Commands ===")
        
        commands = [
            ("get_dims_info", self.mgr.get_dims_info),
            ("get_camera", self.mgr.get_camera),
            ("screenshot", self.mgr.screenshot),
            ("toggle_ndisplay", self.mgr.toggle_ndisplay),
        ]
        
        for name, func in commands:
            logger.info(f"Testing {name}...")
            start_time = time.time()
            success, result = func()
            duration = time.time() - start_time
            
            logger.info(f"{name} took {duration:.2f} seconds")
            if success:
                logger.info(f"✓ {name}: {result}")
            else:
                logger.error(f"✗ {name} failed: {result}")
    
    def load_dataset(self):
        """Load the test dataset."""
        logger.info("=== Loading Test Dataset ===")
        
        if not Path(self.dataset_path).exists():
            logger.error(f"✗ File not found: {self.dataset_path}")
            return False
        
        file_size = Path(self.dataset_path).stat().st_size
        logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
        
        logger.info(f"Loading dataset: {self.dataset_path}")
        start_time = time.time()
        success, result = self.mgr.open_file(self.dataset_path)
        duration = time.time() - start_time
        
        logger.info(f"open_file took {duration:.2f} seconds")
        
        if success:
            logger.info(f"✓ Dataset loaded successfully: {result}")
            
            # Check layers after loading
            success, layers = self.mgr.list_layers()
            if success and layers:
                logger.info(f"✓ Found {len(layers)} layers after loading:")
                for layer in layers:
                    logger.info(f"  - {layer['name']} ({layer['type']})")
            else:
                logger.warning("  No layers found after loading dataset")
                
            return True
        else:
            logger.error(f"✗ Failed to load dataset: {result}")
            return False
    
    def test_step(self, step_name, test_func, *args, **kwargs):
        """Run a single test step with timing."""
        logger.info(f"=== Testing {step_name} ===")
        try:
            start_time = time.time()
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"✓ {step_name} completed in {duration:.2f} seconds")
            return result
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"✗ {step_name} failed after {duration:.2f} seconds: {e}")
            raise
    
    def test_layer_creation_functions(self):
        """Test layer creation functions."""
        logger.info("=== Testing Layer Creation Functions ===")
        
        # Test add_points
        coordinates = [[10, 20], [30, 40], [50, 60]]
        properties = {'label': ['A', 'B', 'C']}
        self.test_step("Add Points", self.mgr.add_points, coordinates, properties, "test_points")
        
        # Test add_shapes
        shape_data = [[[0, 0], [0, 10], [10, 10], [10, 0]]]
        self.test_step("Add Shapes", self.mgr.add_shapes, shape_data, "rectangle", "test_shapes")
        
        # Test add_labels
        label_image = np.zeros((50, 50), dtype=np.uint8)
        label_image[10:20, 10:20] = 1
        label_image[30:40, 30:40] = 2
        self.test_step("Add Labels", self.mgr.add_labels, label_image, "test_labels")
        
        # Test add_surface
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
        ])
        faces = np.array([
            [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
            [0, 4, 7], [0, 7, 3], [1, 5, 6], [1, 6, 2]
        ])
        self.test_step("Add Surface", self.mgr.add_surface, vertices, faces, "test_surface")
        
        # Test add_vectors
        vectors = np.array([[[1, 1], [0, 1]], [[-1, 0], [1, -1]]])
        self.test_step("Add Vectors", self.mgr.add_vectors, vectors, "test_vectors")
    
    def test_data_export_functions(self):
        """Test data export functions."""
        logger.info("=== Testing Data Export Functions ===")
        
        # Create test_files directory if it doesn't exist
        test_files_dir = Path("./test_files")
        test_files_dir.mkdir(exist_ok=True)
        
        # Get layer data
        success, layers = self.mgr.list_layers()
        if success and layers:
            layer_name = layers[0]['name']
            self.test_step("Get Layer Data", self.mgr.get_layer_data, layer_name)
        
        self.test_step("Save Layers", self.mgr.save_layers, str(test_files_dir / "test_layers.tif"))
    
    def test_visualization_controls(self):
        """Test visualization control functions."""
        logger.info("=== Testing Visualization Controls ===")
        
        self.test_step("Set Scale Bar", self.mgr.set_scale_bar, True, "um")
        self.test_step("Set Axis Labels", self.mgr.set_axis_labels, ["t", "c", "z", "y", "x"])
        self.test_step("Set View Mode", self.mgr.set_view_mode, "3D")
        
        success, layers = self.mgr.list_layers()
        if success and layers:
            layer_name = layers[0]['name']
            self.test_step("Set Layer Visibility", self.mgr.set_layer_visibility, layer_name, False)
            self.test_step("Set Layer Visibility", self.mgr.set_layer_visibility, layer_name, True)
    
    def test_measurement_functions(self):
        """Test measurement functions."""
        logger.info("=== Testing Measurement Functions ===")
        
        self.test_step("Measure Distance", self.mgr.measure_distance, [0, 0, 0], [3, 4, 0])
        
        success, layers = self.mgr.list_layers()
        if success and layers:
            layer_name = layers[0]['name']
            self.test_step("Get Layer Statistics", self.mgr.get_layer_statistics, layer_name)
            self.test_step("Crop Layer", self.mgr.crop_layer, layer_name, [0, 1, 0, 1, 0, 10, 0, 10])
    
    def test_time_series_functions(self):
        """Test time series functions."""
        logger.info("=== Testing Time Series Functions ===")
        
        self.test_step("Set Channel", self.mgr.set_channel, 0)
        self.test_step("Set Z Slice", self.mgr.set_z_slice, 0)
        self.test_step("Set Timestep", self.mgr.set_timestep, 0)
        #self.test_step("Play Animation", self.mgr.play_animation, 0, 5, 2)
    
    def test_camera_functions(self):
        """Test camera functions."""
        logger.info("=== Testing Camera Functions ===")
        
        self.test_step("Set Camera", self.mgr.set_camera, [50, 50, 25], 2.0, [30, 45, 60])
        self.test_step("Reset Camera", self.mgr.reset_camera)
    
    def test_layer_management_functions(self):
        """Test layer management functions."""
        logger.info("=== Testing Layer Management Functions ===")
        
        success, layers = self.mgr.list_layers()
        if success and layers:
            layer_name = layers[0]['name']
            self.test_step("Set Colormap", self.mgr.set_colormap, layer_name, "viridis")
            self.test_step("Set Opacity", self.mgr.set_opacity, layer_name, 0.7)
            self.test_step("Set Blending", self.mgr.set_blending, layer_name, "additive")
            self.test_step("Set Contrast Limits", self.mgr.set_contrast_limits, layer_name, 0.1, 0.9)
            self.test_step("Auto Contrast", self.mgr.auto_contrast, layer_name)
            self.test_step("Set Gamma", self.mgr.set_gamma, layer_name, 0.8)
            self.test_step("Set Interpolation", self.mgr.set_interpolation, layer_name, "linear")
    
    def test_view_control_functions(self):
        """Test view control functions."""
        logger.info("=== Testing View Control Functions ===")
        
        self.test_step("Toggle N-Display", self.mgr.toggle_ndisplay)
        self.test_step("Set View Mode", self.mgr.set_view_mode, "3D")
        self.test_step("Toggle N-Display", self.mgr.toggle_ndisplay)  # Toggle back
    
    def test_screenshot_functions(self):
        """Test screenshot functions."""
        logger.info("=== Testing Screenshot Functions ===")
        
        # Create test_files directory if it doesn't exist
        test_files_dir = Path("./test_files")
        test_files_dir.mkdir(exist_ok=True)
        
        self.test_step("Take Screenshot", self.mgr.screenshot)
        self.test_step("Export Screenshot", self.mgr.export_screenshot, str(test_files_dir / "test_screenshot.png"), True)
    
    def test_iso_surface_functions(self):
        """Test iso-surface functions."""
        logger.info("=== Testing Iso-Surface Functions ===")
        
        success, layers = self.mgr.list_layers()
        if success and layers:
            layer_name = layers[0]['name']
            # Test with just layer name first
            self.test_step("Apply Iso-Contour (layer only)", self.mgr.iso_contour, layer_name)
            # Test with just threshold (applies to all layers)
            self.test_step("Apply Iso-Contour (threshold only)", self.mgr.iso_contour_all_layers, 0.5)
            # Test with both layer name and threshold
            self.test_step("Apply Iso-Contour (layer + threshold)", self.mgr.iso_contour, layer_name, 0.5)
    
    def test_layer_removal_functions(self):
        """Test layer removal functions."""
        logger.info("=== Testing Layer Removal Functions ===")
        
        # First add a test layer to remove
        coordinates = [[100, 100], [200, 200]]
        properties = {'label': ['Test1', 'Test2']}
        self.test_step("Add Test Points for Removal", self.mgr.add_points, coordinates, properties, "test_removal_points")
        
        # Now test removal
        success, layers = self.mgr.list_layers()
        if success and layers:
            # Find our test layer
            test_layer = None
            for layer in layers:
                if layer.get('name') == 'test_removal_points':
                    test_layer = layer
                    break
            
            if test_layer:
                self.test_step("Remove Layer by Name", self.mgr.remove_layer, "test_removal_points")
            else:
                logger.warning("Test layer not found for removal test")
    
    def cleanup_test_files(self):
        """Clean up test files created during testing."""
        if self.keep_test_files:
            logger.info("=== Keeping test files as requested ===")
            test_files_dir = Path("./test_files")
            if test_files_dir.exists():
                logger.info(f"  Test files preserved in: {test_files_dir.absolute()}")
            return
        
        logger.info("=== Cleaning up test files ===")
        
        # Clean up files in test_files directory
        test_files_dir = Path("./test_files")
        if test_files_dir.exists():
            test_files = ["test_screenshot.png", "test_layers.tif"]
            for file_name in test_files:
                file_path = test_files_dir / file_name
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"  Removed: {file_path}")
            
            # Remove the test_files directory if it's empty
            try:
                test_files_dir.rmdir()
                logger.info(f"  Removed empty directory: {test_files_dir}")
            except OSError:
                logger.info(f"  Directory {test_files_dir} not empty, keeping it")
        
        # Also clean up any screenshot files that might have been created by the screenshot() function
        import glob
        screenshot_files = glob.glob("screenshot_*.jpg")
        for file_path in screenshot_files:
            if Path(file_path).exists():
                Path(file_path).unlink()
                logger.info(f"  Removed: {file_path}")
    
    def run(self):
        """Run all tests."""
        logger.info(f"Starting consolidated tests (timeout: {self.timeout}s)")
        
        try:
            # Create manager
            if not self.create_manager():
                return False
            
            # Test basic functions
            if not self.test_basic_connection():
                return False
            
            self.test_simple_commands()
            
            # Load dataset and run comprehensive tests
            dataset_loaded = self.load_dataset()
            
            if dataset_loaded:
                logger.info("Dataset loaded successfully - running comprehensive tests...")
                
                self.test_layer_creation_functions()
                self.test_data_export_functions()
                self.test_visualization_controls()
                self.test_measurement_functions()
                self.test_time_series_functions()
                self.test_camera_functions()
                self.test_layer_management_functions()
                self.test_view_control_functions()
                self.test_screenshot_functions()
                self.test_iso_surface_functions()
                self.test_layer_removal_functions()
            else:
                logger.warning("Dataset not loaded - skipping tests that require loaded layers")
            
            self.cleanup_test_files()
            
            logger.info("=== All tests completed successfully ===")
            return True
            
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            import traceback
            logger.error("Full traceback:")
            traceback.print_exc()
            return False

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Consolidated NapariManager test suite")
    parser.add_argument("--timeout", type=float, default=30.0,
                       help="Timeout in seconds (default: 30.0)")
    parser.add_argument("--dataset", type=str, default=DEFAULT_DATASET_PATH,
                       help="Path to test dataset")
    parser.add_argument("--keep-test-files", action="store_true",
                       help="Keep test files after test completion (default: delete them)")
    
    args = parser.parse_args()
    
    runner = TestRunner(
        timeout=args.timeout,
        dataset_path=args.dataset,
        keep_test_files=args.keep_test_files
    )
    
    success = runner.run()
    return 0 if success else 1

if __name__ == "__main__":
    main() 