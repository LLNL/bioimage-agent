#!/usr/bin/env python3
"""
Test script to demonstrate the improved error handling in the napari MCP server.

This script shows how the new error handling system categorizes errors and provides
recovery suggestions to help LLMs understand and respond to failures.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from napari_mcp.napari_manager import NapariManager, NapariError, ErrorType

def test_error_handling():
    """Test various error scenarios to demonstrate the improved error handling."""
    
    print("🧪 Testing Napari MCP Error Handling\n")
    
    # Create manager with shorter timeout for testing
    manager = NapariManager(timeout=2.0, max_retries=2)
    
    print("1. Testing connection health...")
    success, result = manager.test_connection()
    if success:
        print(f"   ✅ {result}")
    else:
        print(f"   ❌ {result}")
    
    print("\n2. Testing file not found error...")
    success, result = manager.open_file("/nonexistent/file.tif")
    if not success and isinstance(result, NapariError):
        print(f"   Error Type: {result.error_type.value}")
        print(f"   Message: {result.message}")
        print(f"   Context: {result.context}")
        print(f"   Suggestion: {result.recovery_suggestion}")
    
    print("\n3. Testing layer not found error...")
    success, result = manager.remove_layer("nonexistent_layer")
    if not success and isinstance(result, NapariError):
        print(f"   Error Type: {result.error_type.value}")
        print(f"   Message: {result.message}")
        print(f"   Context: {result.context}")
        print(f"   Suggestion: {result.recovery_suggestion}")
    
    print("\n4. Testing invalid layer index error...")
    success, result = manager.set_colormap(999, "gray")
    if not success and isinstance(result, NapariError):
        print(f"   Error Type: {result.error_type.value}")
        print(f"   Message: {result.message}")
        print(f"   Context: {result.context}")
        print(f"   Suggestion: {result.recovery_suggestion}")
    
    print("\n5. Testing connection timeout (if napari is not running)...")
    try:
        success, result = manager.list_layers()
        if success:
            print("   ✅ Connection successful")
        else:
            print(f"   ❌ {result}")
    except NapariError as e:
        print(f"   Error Type: {e.error_type.value}")
        print(f"   Message: {e.message}")
        print(f"   Context: {e.context}")
        print(f"   Suggestion: {e.recovery_suggestion}")
    
    print("\n6. Testing error formatting...")
    # Create a sample error
    sample_error = NapariError(
        ErrorType.LAYER_ERROR,
        "Layer 'my_layer' not found",
        {"layer_name": "my_layer", "available_layers": ["layer1", "layer2"]},
        "Use list_layers() to see available layers and their correct names"
    )
    
    print("   Sample formatted error:")
    print(f"   {sample_error.to_dict()}")
    
    print("\n✅ Error handling test completed!")
    print("\nKey improvements:")
    print("• 🔌 Connection errors with retry logic")
    print("• 📁 File errors with path validation")
    print("• 🖼️ Layer errors with context about available layers")
    print("• ❌ Validation errors with parameter checking")
    print("• 💡 Recovery suggestions for each error type")
    print("• 🔄 Automatic retry for transient failures")

if __name__ == "__main__":
    test_error_handling()
