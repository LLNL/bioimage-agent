from pathlib import Path
from napari.viewer import Viewer
import numpy as np

def open_file(
    path: str | Path,                 # ① first (supplied by you)
    viewer: Viewer,                   # ② injected by napari
    *,                                # keyword-only from here on
    plugin: str | None = None,
    layer_type: str | None = None,
):
    """Open *any* image file (TIFF, PNG, ND2…) with napari’s readers."""
    layers = viewer.open(
        Path(path),
        plugin=plugin or "napari",     # built-in reader first
        layer_type=layer_type,
    )
    return layers[0] if layers else None


def open_npz(
    path: str | Path,
    array_name: str | None = None,          # ← your 2nd positional arg
    *,
    viewer: Viewer,                         # ← injected by napari
    as_points: bool = False,
):
    """Load an .npz file and add one array as a layer."""
    with np.load(Path(path)) as data:
        if array_name is None:
            array_name = next(iter(data))   # first key
        arr = data[array_name]

    if as_points:
        layer = viewer.add_points(arr, name=array_name)
    else:
        layer = viewer.add_image(arr, name=array_name)
    return layer

def remove_layer(name_or_index: str | int, viewer: Viewer):
    """Remove a layer by its name or positional index."""
    layers = viewer.layers
    if isinstance(name_or_index, int):
        layer = layers[name_or_index]
    else:
        layer = layers[name_or_index]
    viewer.layers.remove(layer)