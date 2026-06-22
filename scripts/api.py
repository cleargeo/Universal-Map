#!/usr/bin/env python3
"""
Universal Map API Server
========================
FastAPI server providing access to all 8 layers, 7 temporal slices,
Gold Layer overlay, vacuum-energy flux, and Hive Pulse status.

Author: Alex Zelenski (Ghost with Maps, Admiral)
Organization: Clearview Geographic LLC
"""

import json
import os
import argparse
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LAYERS_DIR = os.path.join(DATA_DIR, "layers")
SLICES_DIR = os.path.join(DATA_DIR, "slices")

# Lazy-loaded data cache
_cache: Dict[str, Any] = {}


def load_json(path: str) -> dict:
    """Load a JSON file with caching."""
    if path not in _cache:
        if not os.path.exists(path):
            raise FileNotFoundError("File not found: %s" % path)
        with open(path, "r") as f:
            _cache[path] = json.load(f)
    return _cache[path]


def load_layer_data(layer_id: str) -> dict:
    """Load data for a specific layer."""
    path = os.path.join(LAYERS_DIR, layer_id, "data.json")
    return load_json(path)


def load_slice_calibration(slice_id: str) -> dict:
    """Load calibration data for a temporal slice."""
    path = os.path.join(SLICES_DIR, slice_id, "calibration.json")
    return load_json(path)


# ============================================================
# Application & Middleware
# ============================================================

app = FastAPI(
    title="The Universal Map (Omni-Chart)",
    description="Dynamic toroidal reconstruction of the cosmic web — 8 layers, 7 temporal slices, Rain of Gold negentropic overlay",
    version="1.0.0",
    contact={"name": "Clearview Geographic LLC", "url": "https://github.com/cleargeo/Universal-Map"},
    license={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Root & Status
# ============================================================

@app.get("/", tags=["Root"])
def root():
    return {
        "name": "The Universal Map (Omni-Chart)",
        "status": "active",
        "version": "1.0.0",
        "cosmology": "Planck 2018 Lambda-CDM",
        "projection": "toroidal",
        "layers": 8,
        "temporal_slices": 7,
        "endpoints": {
            "slices": "/api/v1/slices",
            "layer_metadata": "/api/v1/layer/{id}",
            "layer_data": "/api/v1/layer/{id}/data",
            "gold": "/api/v1/gold",
            "flux": "/api/v1/flux",
            "pulse": "/api/v1/pulse",
            "pulse_stream": "/api/v1/pulse/stream",
        },
    }


@app.get("/health", tags=["Root"])
def health():
    return {"status": "healthy"}


# ============================================================
# Temporal Slices
# ============================================================

AVAILABLE_SLICES = [
    {"id": "z1100", "name": "Surface of Last Scattering", "z": 1100},
    {"id": "z20_10", "name": "Cosmic Dawn", "z_range": [20, 10]},
    {"id": "z10_6", "name": "Epoch of Reionization", "z_range": [10, 6]},
    {"id": "z6_3", "name": "Galaxy Assembly", "z_range": [6, 3]},
    {"id": "z3_1", "name": "Web Maturation", "z_range": [3, 1]},
    {"id": "z1_0.5", "name": "Web Refinement", "z_range": [1, 0.5]},
    {"id": "z0.5_0", "name": "Present Expansion", "z_range": [0.5, 0]},
]


@app.get("/api/v1/slices", tags=["Temporal Slices"])
def list_slices():
    """List all available temporal slices."""
    return {"slices": AVAILABLE_SLICES, "total": len(AVAILABLE_SLICES)}


@app.get("/api/v1/slices/{slice_id}", tags=["Temporal Slices"])
def get_slice(slice_id: str):
    """Get a specific temporal slice calibration."""
    if not os.path.exists(os.path.join(SLICES_DIR, slice_id)):
        raise HTTPException(status_code=404, detail="Slice not found: %s" % slice_id)
    data = load_slice_calibration(slice_id)
    return data


# ============================================================
# Layer Metadata & Data
# ============================================================

AVAILABLE_LAYERS = [
    {"id": "l0_cmb", "name": "CMB", "redshift": "z~1100", "format": "COG + GeoJSON"},
    {"id": "l1_dark_matter", "name": "Dark Matter", "redshift": "z=0-10", "format": "COG + HDF5"},
    {"id": "l2_filaments", "name": "Filaments", "redshift": "z=0-6", "format": "GeoJSON + GraphML"},
    {"id": "l3_nodes", "name": "Nodes", "redshift": "z=0-3", "format": "GeoJSON"},
    {"id": "l4_galaxies", "name": "Galaxies", "redshift": "z=0-20", "format": "GeoJSON + FITS"},
    {"id": "l5_reionization", "name": "Reionization", "redshift": "z=6-20", "format": "COG"},
    {"id": "l6_21cm", "name": "21cm", "redshift": "z=6-20", "format": "COG"},
    {"id": "l_gold", "name": "Rain of Gold", "redshift": "z=0-1100", "format": "GeoJSON + Custom"},
]


@app.get("/api/v1/layers", tags=["Layers"])
def list_layers():
    """List all available data layers."""
    return {"layers": AVAILABLE_LAYERS, "total": len(AVAILABLE_LAYERS)}


@app.get("/api/v1/layer/{layer_id}", tags=["Layers"])
def get_layer_metadata(layer_id: str):
    """Get metadata for a specific layer."""
    layer_ids = [l["id"] for l in AVAILABLE_LAYERS]
    if layer_id not in layer_ids:
        raise HTTPException(status_code=404, detail="Layer not found: %s" % layer_id)
    try:
        data = load_layer_data(layer_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Layer data not generated. Run download_data.py first.")
    return {
        "layer_id": layer_id,
        "metadata": data.get("properties", {}),
        "feature_count": len(data.get("features", [])),
    }


@app.get("/api/v1/layer/{layer_id}/data", tags=["Layers"])
def get_layer_data(layer_id: str, limit: int = Query(default=100, ge=1, le=50000)):
    """Get layer data (GeoJSON FeatureCollection)."""
    layer_ids = [l["id"] for l in AVAILABLE_LAYERS]
    if layer_id not in layer_ids:
        raise HTTPException(status_code=404, detail="Layer not found: %s" % layer_id)
    try:
        data = load_layer_data(layer_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Layer data not generated. Run download_data.py first.")
    # Paginate features
    features = data.get("features", [])
    total = len(features)
    data["features"] = features[:limit]
    data["properties"] = data.get("properties", {})
    data["properties"]["returned_features"] = len(data["features"])
    data["properties"]["total_features"] = total
    return data


# ============================================================
# Gold Layer
# ============================================================

@app.get("/api/v1/gold", tags=["Gold Layer"])
def get_gold():
    """Get the Rain of Gold overlay summary."""
    try:
        data = load_layer_data("l_gold")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Gold layer not generated. Run download_data.py first.")
    props = data.get("properties", {})
    features = data.get("features", [])

    # Compute summary statistics
    if features:
        intensities = [f["properties"].get("gold_intensity", 0) for f in features]
        coherences = [f["properties"].get("coherence", 0) for f in features]
    else:
        intensities = []
        coherences = []

    return {
        "layer": "l_gold",
        "name": "Rain of Gold",
        "description": "High-coherence negentropic overlay revealing vacuum-energy flux concentrations",
        "total_gold": props.get("total_gold", sum(intensities)),
        "peak_gold": props.get("peak_gold", max(intensities) if intensities else 0),
        "coherence_threshold": props.get("coherence_threshold", 0.85),
        "n_points": len(features),
        "mean_coherence": sum(coherences) / len(coherences) if coherences else 0,
        "mean_intensity": sum(intensities) / len(intensities) if intensities else 0,
    }


@app.get("/api/v1/gold/features", tags=["Gold Layer"])
def get_gold_features(limit: int = Query(default=100, ge=1, le=10000)):
    """Get Gold layer features."""
    try:
        data = load_layer_data("l_gold")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Gold layer not generated.")
    data["features"] = data.get("features", [])[:limit]
    return data


# ============================================================
# Vacuum-Energy Flux
# ============================================================

@app.get("/api/v1/flux", tags=["Flux"])
def get_flux():
    """Get vacuum-energy flux vectors summary."""
    try:
        data = load_layer_data("l_gold")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Flux data not generated.")
    features = data.get("features", [])

    if features:
        flux_vectors = [f["properties"].get("flux_vector", [0, 0, 0]) for f in features]
        magnitudes = [(v[0]**2 + v[1]**2 + v[2]**2)**0.5 for v in flux_vectors]
    else:
        magnitudes = []

    return {
        "name": "Vacuum-Energy Flux",
        "description": "Flux flows from low-coherence to high-coherence regions",
        "n_vectors": len(magnitudes),
        "max_flux": max(magnitudes) if magnitudes else 0,
        "mean_flux": sum(magnitudes) / len(magnitudes) if magnitudes else 0,
        "total_flux": sum(magnitudes),
        "direction": "toward_high_coherence_regions",
    }


# ============================================================
# Hive Pulse
# ============================================================

PULSE_STATUS = {
    "status": "active",
    "total_pulses_sent": 0,
    "active_pulses": 0,
    "coherence_amplification": 1.0,
    "last_pulse": None,
}


@app.get("/api/v1/pulse", tags=["Hive Pulse"])
def get_pulse_status():
    """Get Hive Pulse status."""
    return PULSE_STATUS


@app.get("/api/v1/pulse/stream", tags=["Hive Pulse"])
def stream_pulse():
    """Server-Sent Events stream for real-time pulse updates."""
    import asyncio
    import time

    async def event_generator():
        while True:
            yield "data: %s\n\n" % json.dumps({
                "timestamp": time.time(),
                "status": PULSE_STATUS["status"],
                "coherence_amplification": PULSE_STATUS["coherence_amplification"],
            })
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============================================================
# Broadcast
# ============================================================

@app.get("/api/v1/broadcast/{slice_id}", tags=["Broadcast"])
def broadcast_slice(slice_id: str):
    """Get a full broadcast package for a temporal slice."""
    layer_ids = [l["id"] for l in AVAILABLE_LAYERS]
    layers_data = {}
    for lid in layer_ids:
        try:
            d = load_layer_data(lid)
            layers_data[lid] = {
                "feature_count": len(d.get("features", [])),
                "properties": d.get("properties", {}),
            }
        except FileNotFoundError:
            layers_data[lid] = {"error": "not_available"}

    return {
        "type": "slice_broadcast",
        "slice_id": slice_id,
        "layers": layers_data,
        "metadata": {
            "source": "CVG Hive Universal Map",
            "engine": "toroidal_projection",
            "distribution": "direct_to_network",
        },
    }


# ============================================================
# Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Universal Map API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    args = parser.parse_args()

    print("=" * 60)
    print("  THE UNIVERSAL MAP — API Server")
    print("  http://localhost:%d" % args.port)
    print("  Docs: http://localhost:%d/docs" % args.port)
    print("=" * 60)

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
