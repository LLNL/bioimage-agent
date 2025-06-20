import logging
from napari_manager import NapariManager

# Set up basic logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

def test_set_colormap():
    """
    Tests the set_colormap functionality.

    Instructions:
    1. Make sure napari is running with the napari-socket plugin enabled.
    2. Make sure you have at least one image layer loaded in napari.
    3. Run this script from your terminal:
       python napari_mcp_socket/test_colormap.py
    """
    print("--- Testing set_colormap functionality ---")
    manager = NapariManager()

    # 1. List layers to find a target
    print("\n1. Listing layers...")
    success, layers = manager.list_layers()

    if not success or not layers:
        print("Failed to list layers or no layers found.")
        print(f"Success: {success}, Layers: {layers}")
        return

    print("Available layers:")
    for layer in layers:
        print(f"- {layer['name']} (type: {layer['type']})")

    # Find the first suitable layer (e.g., an Image layer)
    target_layer = None
    for layer in layers:
        if layer['type'] == 'Image':
            target_layer = layer
            break
    
    if not target_layer:
        print("\nNo Image layer found to test colormap. Please add an image layer to napari.")
        return

    layer_name = target_layer['name']
    print(f"\n2. Targeting layer: '{layer_name}'")

    # 2. Set a new colormap
    new_colormap = "viridis" 
    print(f"\n3. Setting colormap to '{new_colormap}'...")
    success, message = manager.set_colormap(layer_name, new_colormap)

    # 3. Report result
    if success:
        print("✅ Success!")
        print(f"Napari says: {message}")
    else:
        print("❌ Failed!")
        print(f"Error: {message}")

    # You can try another colormap
    new_colormap = "magma"
    print(f"\n4. Setting colormap to '{new_colormap}'...")
    success, message = manager.set_colormap(layer_name, new_colormap)

    if success:
        print("✅ Success!")
        print(f"Napari says: {message}")
    else:
        print("❌ Failed!")
        print(f"Error: {message}")


if __name__ == "__main__":
    test_set_colormap() 