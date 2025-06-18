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

def toggle_ndisplay(viewer: Viewer):
    """Toggle napari between 2-D (ndisplay = 2) and 3-D (ndisplay = 3)."""
    viewer.dims.ndisplay = 3 if viewer.dims.ndisplay == 2 else 2
    return viewer.dims.ndisplay


# ----------------------------------------------------------------------
# iso-surface (contour) rendering
# ----------------------------------------------------------------------

def iso_contour(
    layer_name: str | int | None = None,
    viewer: Viewer | None = None,          # injected by napari
    threshold: float | None = None,
) -> int:
    """
    Switch the specified image/volume layer (or all render-capable layers)
    to *iso* rendering and optionally set the ``iso_threshold``.

    Returns
    -------
    int
        Number of layers that were modified.
    """
    # ensure a 3-D canvas so the surface is visible
    if viewer.dims.ndisplay != 3:
        viewer.dims.ndisplay = 3

    # resolve which layers to edit
    if layer_name is None:
        targets = [lyr for lyr in viewer.layers if hasattr(lyr, "rendering")]
    else:
        targets = [
            viewer.layers[layer_name] if isinstance(layer_name, int) else viewer.layers[layer_name]
        ]

    # apply rendering mode / threshold
    for lyr in targets:
        lyr.rendering = "iso"
        if threshold is not None and hasattr(lyr, "iso_threshold"):
            lyr.iso_threshold = threshold

    return len(targets)