from pathlib import Path
from napari.viewer import Viewer
import numpy as np
import collections.abc
import json

def open_file(
    path: str | Path,                 # ① first (supplied by you)
    viewer: Viewer,                   # ② injected by napari
    *,                                # keyword-only from here on
    plugin: str | None = None,
    layer_type: str | None = None,
):
    """Open *any* image file (TIFF, PNG, ND2…) with napari's readers."""
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


# ----------------------------------------------------------------------
# screenshot helper
# ----------------------------------------------------------------------

def screenshot(
    path: str | None = None,
    viewer: Viewer | None = None,          # injected by napari
    canvas_only: bool = True,
) -> str:
    """
    Capture a PNG screenshot of the current napari viewer.

    Parameters
    ----------
    path : str | None
        If given, save the screenshot to this location *on the napari host*.
        Otherwise a temporary file is created and its absolute path returned.
    canvas_only : bool
        Capture just the rendering canvas (default) or the full UI.

    Returns
    -------
    str
        Absolute path to the saved PNG.
    """
    import os, tempfile

    if path is None:
        fd, tmp = tempfile.mkstemp(prefix="napari_scr_", suffix=".png")
        os.close(fd)
        path = tmp

    viewer.screenshot(path=path, canvas_only=canvas_only)
    return os.path.abspath(path)

# ----------------------------------------------------------------------
# layer introspection
# ----------------------------------------------------------------------

def to_serializable(obj):
    """Recursively convert an object to something JSON-serializable."""
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {str(k): to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [to_serializable(v) for v in obj]
    # numpy types
    elif hasattr(obj, 'item') and callable(obj.item):
        try:
            return obj.item()
        except Exception:
            return str(obj)
    # fallback: string representation
    return str(obj)

def list_layers(viewer: Viewer):
    """
    Return information about all loaded layers.

    Returns
    -------
    list[dict]
        One dict per layer with ``index``, ``name``, ``type``, and ``visible``.
    """
    result = to_serializable([
        {
            "index": i,
            "name": layer.name,
            "type": layer.__class__.__name__,
            "visible": layer.visible,
        }
        for i, layer in enumerate(viewer.layers)
    ])

    # If result is a Future, get its result
    if hasattr(result, "result") and callable(result.result):
        try:
            result = result.result(timeout=5)
        except Exception as e:
            return f"ERR {e}\n"

    try:
        payload = json.dumps(result)
        reply: bytes = f"OK {payload}\n".encode()
    except TypeError:                # result not JSON-serialisable
        reply = b"OK\n"
    
    return reply.decode()