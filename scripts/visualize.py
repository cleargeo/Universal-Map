#!/usr/bin/env python3
"""
Universal Map Visualization
============================
Renders all 8 layers on a toroidal projection with Gold overlay.
Supports interactive 3D view, temporal scrubbing, and layer toggling.

Author: Alex Zelenski (Ghost with Maps, Admiral)
Organization: Clearview Geographic LLC
"""

import json
import os
import argparse
import sys

import numpy as np

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from universal_map.toroidal_projection import CosmologyEngine, ToroidalProjector, RedshiftSlicer

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LAYERS_DIR = os.path.join(DATA_DIR, "layers")


def load_layer(layer_id: str) -> dict:
    """Load layer data from disk."""
    path = os.path.join(LAYERS_DIR, layer_id, "data.json")
    if not os.path.exists(path):
        print("  [WARN] Layer data not found: %s" % layer_id)
        return None
    with open(path, "r") as f:
        return json.load(f)


def render_toroidal_ascii(data: dict, layer_id: str, width: int = 70, height: int = 20) -> str:
    """Render a layer as ASCII toroidal projection."""
    if not data:
        return "  [No data for %s]" % layer_id

    features = data.get("features", [])
    if not features:
        return "  [Empty layer: %s]" % layer_id

    # Extract coordinates
    coords = []
    for f in features:
        geom = f.get("geometry", {})
        if geom.get("type") == "Point":
            c = geom.get("coordinates", [0, 0, 0])
            coords.append(c[:2])  # Use x, y for 2D projection

    if not coords:
        return "  [No point features in %s]" % layer_id

    coords = np.array(coords)

    # Normalize to 0-1 range
    x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
    y_min, y_max = coords[:, 1].min(), coords[:, 1].max()

    if x_max == x_min or y_max == y_min:
        return "  [Degenerate coordinates in %s]" % layer_id

    x_norm = (coords[:, 0] - x_min) / (x_max - x_min)
    y_norm = (coords[:, 1] - y_min) / (y_max - y_min)

    # Map to toroidal coordinates (theta, phi)
    theta = x_norm * 2 * np.pi  # toroidal angle
    phi = y_norm * np.pi  # poloidal angle

    # Project to 2D (unfold torus)
    grid = [[" " for _ in range(width)] for _ in range(height)]

    for t, p in zip(theta, phi):
        col = int(t / (2 * np.pi) * (width - 1))
        row = int(p / np.pi * (height - 1))
        row = min(max(row, 0), height - 1)
        col = min(max(col, 0), width - 1)
        grid[row][col] = "*"

    # Build output
    lines = []
    lines.append("  +%s+" % "-" * width)
    for row in grid:
        lines.append("  |%s|" % "".join(row))
    lines.append("  +%s+" % "-" * width)
    lines.append("  %s (%d points)" % (layer_id, len(coords)))
    return "\n".join(lines)


def render_toroidal_matplotlib(data: dict, layer_id: str, output_path: str = None):
    """Render a layer using matplotlib (if available)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [matplotlib not available — use ASCII mode]")
        return

    if not data:
        return

    features = data.get("features", [])
    if not features:
        return

    # Extract coordinates and a property for coloring
    coords = []
    values = []
    for f in features:
        geom = f.get("geometry", {})
        if geom.get("type") == "Point":
            c = geom.get("coordinates", [0, 0, 0])
            coords.append(c[:2])
            # Use first numeric property for color
            props = f.get("properties", {})
            val = 0
            for v in props.values():
                if isinstance(v, (int, float)):
                    val = v
                    break
            values.append(val)

    if not coords:
        return

    coords = np.array(coords)
    values = np.array(values)

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    # Toroidal projection: theta = longitude mapped to 0-2pi, phi = latitude to 0-pi
    x_norm = (coords[:, 0] - coords[:, 0].min()) / (coords[:, 0].max() - coords[:, 0].min() + 1e-10)
    y_norm = (coords[:, 1] - coords[:, 1].min()) / (coords[:, 1].max() - coords[:, 1].min() + 1e-10)

    theta = x_norm * 2 * np.pi
    phi = y_norm * np.pi

    # 3D toroidal surface
    R, r = 1.0, 0.3
    X = (R + r * np.cos(phi)) * np.cos(theta)
    Y = (R + r * np.cos(phi)) * np.sin(theta)
    Z = r * np.sin(phi)

    scatter = ax.scatter(X, Y, Z, c=values, cmap="inferno", s=1, alpha=0.6)
    ax.set_xlabel("X (toroidal)")
    ax.set_ylabel("Y (toroidal)")
    ax.set_zlabel("Z (poloidal)")
    ax.set_title("Universal Map — %s" % layer_id)
    plt.colorbar(scatter, label="Value", shrink=0.5)

    if output_path:
        plt.savefig(output_path, dpi=100, bbox_inches="tight")
        print("  Saved: %s" % output_path)
    else:
        output = "output_%s.png" % layer_id
        plt.savefig(output, dpi=100, bbox_inches="tight")
        print("  Saved: %s" % output)
    plt.close()


def visualize_all(mode: str = "ascii", layer: str = "all"):
    """Visualize layers in the specified mode."""
    cosmo = CosmologyEngine()
    projector = ToroidalProjector()
    slicer = RedshiftSlicer(cosmo)

    print("=" * 60)
    print("  THE UNIVERSAL MAP — Visualization")
    print("  Mode: %s | Layer: %s" % (mode, layer))
    print("=" * 60)

    # Show cosmology
    print("\nCosmological Distances:")
    for z in [0, 0.5, 1, 3, 6, 10, 1100]:
        d = cosmo.comoving_distance(z)
        t = cosmo.lookback_time(z)
        print("  z=%-6s  D_C=%-8.0f Mpc/h  t_lookback=%-6.2f Gyr" % (z, d, t))

    # Show temporal slices
    print("\nTemporal Slices:")
    for s in slicer.SLICES:
        z = s.get("z", s.get("z_range", "?"))
        print("  %-30s z=%s" % (s["name"], z))

    # Load and render layers
    layers_to_render = []
    if layer == "all":
        layers_to_render = ["l0_cmb", "l1_dark_matter", "l2_filaments", "l3_nodes",
                           "l4_galaxies", "l5_reionization", "l6_21cm", "l_gold"]
    else:
        layers_to_render = [layer]

    print("\nRendering layers...")
    for layer_id in layers_to_render:
        data = load_layer(layer_id)
        if data is None:
            continue

        if mode == "ascii":
            print("\n%s" % render_toroidal_ascii(data, layer_id))
        elif mode == "3d":
            render_toroidal_matplotlib(data, layer_id)
        elif mode == "summary":
            props = data.get("properties", {})
            n_features = len(data.get("features", []))
            print("  %s: %d features" % (layer_id, n_features))
            for k, v in props.items():
                if k not in ("n_points",):
                    print("    %s: %s" % (k, v))

    print("\nVisualization complete.")


def main():
    parser = argparse.ArgumentParser(description="Universal Map Visualization")
    parser.add_argument("--mode", choices=["ascii", "3d", "summary"], default="ascii",
                        help="Rendering mode")
    parser.add_argument("--layer", default="all", help="Layer ID to visualize (default: all)")
    args = parser.parse_args()

    visualize_all(mode=args.mode, layer=args.layer)


if __name__ == "__main__":
    main()
