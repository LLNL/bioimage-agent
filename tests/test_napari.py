import napari, numpy as np

viewer = napari.Viewer()
viewer.add_image(np.random.rand(200, 300))

# 2-D: center on the lower-right quadrant and zoom in
viewer.camera.center = (150, 100, 0)
viewer.camera.zoom = 2.0

# Switch to 3-D and spin the volume
viewer.dims.ndisplay = 3
viewer.camera.angles = (30, 45, 0)      # rx, ry, rz in degrees
viewer.camera.zoom = 1.2

# Use direction vectors instead of Euler angles
# viewer.camera.set_view_direction((1, 0, -1), up=(0, -1, 0))
