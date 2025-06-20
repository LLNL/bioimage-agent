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
) -> dict:
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
    dict
        A dictionary with 'path' and 'base64_data'.
    """
    import os
    import tempfile
    from PIL import Image
    import base64
    import io

    if path is None:
        # get array and save it to a temp file
        screenshot_array = viewer.screenshot(canvas_only=canvas_only)
        img = Image.fromarray(screenshot_array)
        
        fd, tmp = tempfile.mkstemp(prefix="napari_scr_", suffix=".png")
        os.close(fd)
        path = tmp
        img.save(path)
    else:
        # save directly to path
        viewer.screenshot(path=path, canvas_only=canvas_only)
        # read back for base64 encoding
        img = Image.open(path)

    # base64 encode
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return {"path": os.path.abspath(path), "base64_data": img_str}

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
    return to_serializable([
        {
            "index": i,
            "name": layer.name,
            "type": layer.__class__.__name__,
            "visible": layer.visible,
        }
        for i, layer in enumerate(viewer.layers)
    ])

def set_colormap(
    layer_name: str | int,
    colormap: str,
    viewer: Viewer,
):
    """Set the colormap for a given layer."""
    if isinstance(layer_name, int):
        layer = viewer.layers[layer_name]
    else:
        layer = viewer.layers[layer_name]

    if hasattr(layer, 'colormap'):
        layer.colormap = colormap
        return f"Colormap for layer '{layer.name}' set to '{colormap}'."
    
    return f"Layer '{layer.name}' of type {type(layer).__name__} does not have a colormap attribute."

def _get_layer(viewer: Viewer, layer_name: str | int | None = None):
    """Helper to get a layer by name/index or the active layer."""
    if layer_name is not None:
        return viewer.layers[layer_name]
    return viewer.layers.selection.active

def set_opacity(
    layer_name: str | int,
    opacity: float,
    viewer: Viewer,
    ):
    """Set the opacity for a given layer (or the active one)."""
    if isinstance(layer_name, int):
        layer = viewer.layers[layer_name]
    else:
        layer = viewer.layers[layer_name]

    if hasattr(layer, 'opacity'):
        layer.opacity = opacity
        return f"Opacity for layer '{layer.name}' set to {opacity}."
    return f"Layer '{layer.name}' does not have an opacity attribute."

def set_blending(
        layer_name: str | int,
        blending: str,
        viewer: Viewer,
        ):
    """Set the blending mode for a given layer (or the active one)."""
    layer = _get_layer(viewer, layer_name)
    if hasattr(layer, 'blending'):
        layer.blending = blending
        return f"Blending mode for layer '{layer.name}' set to '{blending}'."
    return f"Layer '{layer.name}' does not have a blending attribute."

def set_contrast_limits(
    layer_name: str | int, 
    contrast_min: float, 
    contrast_max: float, 
    viewer: Viewer,
    ):
    """Set the contrast limits for a given layer (or the active one)."""
    layer = _get_layer(viewer, layer_name)
    if hasattr(layer, 'contrast_limits'):
        layer.contrast_limits = (contrast_min, contrast_max)
        return f"Contrast limits for layer '{layer.name}' set to ({contrast_min}, {contrast_max})."
    return f"Layer '{layer.name}' does not have a contrast_limits attribute."

def auto_contrast(
        layer_name: str | int,
        viewer: Viewer, 
    ):
    """Auto-adjust contrast for a given layer (or the active one)."""
    layer = _get_layer(viewer, layer_name)
    if hasattr(layer, 'reset_contrast_limits'):
        layer.reset_contrast_limits()
        return f"Auto-contrasted layer '{layer.name}'. New limits: {layer.contrast_limits}."
    return f"Layer '{layer.name}' does not have auto-contrast capability."

def set_gamma(
        layer_name: str | int, 
        gamma: float, 
        viewer: Viewer, 
        ):
    """Set the gamma for a given layer (or the active one)."""
    layer = _get_layer(viewer, layer_name)
    if hasattr(layer, 'gamma'):
        layer.gamma = gamma
        return f"Gamma for layer '{layer.name}' set to {gamma}."
    return f"Layer '{layer.name}' does not have a gamma attribute."

def set_interpolation(
        layer_name: str | int,
        interpolation: str, 
        viewer: Viewer, 
        ):
    """Set the interpolation for a given layer (or the active one)."""
    layer = _get_layer(viewer, layer_name)
    if hasattr(layer, 'interpolation'):
        layer.interpolation = interpolation
        return f"Interpolation for layer '{layer.name}' set to '{interpolation}'."
    return f"Layer '{layer.name}' does not have an interpolation attribute."

def set_timestep(
    timestep: int,
    viewer: Viewer,
    ):
    """Set the timestep for the viewer."""
    current_step = list(viewer.dims.current_step)
    if not current_step:
        return "Viewer has no dimensions with steps."
    
    if timestep >= viewer.dims.nsteps[0]:
        return f"Timestep {timestep} is out of bounds (max: {viewer.dims.nsteps[0] - 1})."
        
    current_step[0] = timestep
    viewer.dims.current_step = tuple(current_step)
    return f"Timestep set to {timestep}."

def get_dims_info(viewer: Viewer):
    """Get information about the viewer's dimensions."""
    dims_info = {
        'ndim': viewer.dims.ndim,
        'nsteps': viewer.dims.nsteps,
        'current_step': viewer.dims.current_step,
        'axis_labels': list(viewer.dims.axis_labels),
    }
    return to_serializable(dims_info)