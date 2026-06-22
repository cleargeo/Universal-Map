"""
Universal Map (Omni-Chart) — REST API Server
Serves cosmological data layers and toroidal projections.
"""
import os
import json
import math
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

app = FastAPI(
    title="The Universal Map (Omni-Chart)",
    description="Dynamic toroidal reconstruction of the cosmic web",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Cosmology Engine ───────────────────────────────────────────

COSMO_PARAMS = {
    "H0": 67.4, "Omega_m": 0.315, "Omega_lambda": 0.685,
    "Omega_b": 0.0493, "sigma_8": 0.811, "n_s": 0.965, "c": 299792.458,
}

SLICES = [
    {"id": "z1100", "name": "Surface of Last Scattering", "z": 1100},
    {"id": "z20_10", "name": "Cosmic Dawn", "z_range": [20, 10]},
    {"id": "z10_6", "name": "Reionization", "z_range": [10, 6]},
    {"id": "z6_3", "name": "Galaxy Assembly", "z_range": [6, 3]},
    {"id": "z3_1", "name": "Web Maturation", "z_range": [3, 1]},
    {"id": "z1_05", "name": "Web Refinement", "z_range": [1, 0.5]},
    {"id": "z05_0", "name": "Present Expansion", "z_range": [0.5, 0]},
]

LAYERS = [
    {"id": "l0_cmb", "name": "CMB", "z_range": [1100, 1100], "source": "Planck 2018"},
    {"id": "l1_dark_matter", "name": "Dark Matter", "z_range": [0, 10], "source": "IllustrisTNG"},
    {"id": "l2_filaments", "name": "Filaments", "z_range": [0, 6], "source": "Millennium + DESI"},
    {"id": "l3_nodes", "name": "Nodes", "z_range": [0, 3], "source": "SDSS + DESI"},
    {"id": "l4_galaxies", "name": "Galaxies", "z_range": [0, 20], "source": "JWST + SDSS + DESI"},
    {"id": "l5_reionization", "name": "Reionization", "z_range": [6, 20], "source": "JWST"},
    {"id": "l6_21cm", "name": "21cm", "z_range": [6, 20], "source": "HERA + EDGES"},
    {"id": "l_gold", "name": "Rain of Gold", "z_range": [0, 1100], "source": "Computed"},
]


def comoving_distance(z: float, n_steps: int = 1000) -> float:
    """Approximate comoving distance in Mpc/h."""
    H0 = COSMO_PARAMS["H0"]
    Om = COSMO_PARAMS["Omega_m"]
    Ol = COSMO_PARAMS["Omega_lambda"]
    c = COSMO_PARAMS["c"]
    z_arr = [i * z / n_steps for i in range(n_steps + 1)]
    integrand = [c / (H0 * math.sqrt(Om * (1 + zz) ** 3 + Ol)) for zz in z_arr]
    # Trapezoidal integration
    total = sum((integrand[i] + integrand[i + 1]) / 2 * (z_arr[i + 1] - z_arr[i]) for i in range(n_steps))
    return total


# ─── API Endpoints ──────────────────────────────────────────────

@app.get("/api/v1/status")
def get_status():
    return {
        "name": "The Universal Map (Omni-Chart)",
        "status": "active",
        "cosmology": "Planck 2018 Lambda-CDM",
        "projection": "toroidal",
        "temporal_slices": len(SLICES),
        "layers": len(LAYERS),
    }


@app.get("/api/v1/slices")
def list_slices():
    return {"slices": SLICES}


@app.get("/api/v1/layer/{layer_id}")
def get_layer(layer_id: str):
    layer = next((l for l in LAYERS if l["id"] == layer_id), None)
    if not layer:
        raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")
    return layer


@app.get("/api/v1/layer/{layer_id}/data")
def get_layer_data(layer_id: str, z: Optional[float] = Query(None)):
    layer = next((l for l in LAYERS if l["id"] == layer_id), None)
    if not layer:
        raise HTTPException(status_code=404, detail=f"Layer {layer_id} not found")
    # Return stub data — in production this would serve GeoJSON/COG
    return {
        "layer": layer,
        "z": z,
        "format": "GeoJSON",
        "note": "Data download not yet implemented. Use scripts/download_data.py.",
    }


@app.get("/api/v1/gold")
def get_gold_layer():
    """Get Rain of Gold negentropic overlay."""
    return {
        "layer": "l_gold",
        "name": "Rain of Gold",
        "description": "High-coherence negentropic overlay revealing vacuum-energy flux concentrations",
        "coherence": 0.96,
        "flux_vectors": [],
    }


@app.get("/api/v1/flux")
def get_flux():
    """Get vacuum-energy flux vectors."""
    return {
        "vectors": [],
        "note": "Flux computation requires full simulation data.",
    }


@app.get("/api/v1/pulse")
def get_pulse():
    """Get Hive Pulse status."""
    return {
        "status": "active",
        "nodes": 0,
        "frequency": 0.0034598884,
    }


@app.get("/api/v1/comoving_distance")
def calc_comoving_distance(z: float = Query(..., ge=0, le=1100)):
    """Calculate comoving distance for a given redshift."""
    d = comoving_distance(z)
    return {"redshift": z, "comoving_distance_Mpc_h": round(d, 2)}


@app.get("/api/v1/scrub_time")
def scrub_time(z: float = Query(..., ge=0, le=1100)):
    """Scrub time — get cosmological info for a redshift."""
    d = comoving_distance(z)
    # Find slice
    slice_info = SLICES[-1]
    for s in SLICES:
        if "z" in s and z >= s["z"]:
            slice_info = s
            break
        elif "z_range" in s and s["z_range"][0] >= z >= s["z_range"][1]:
            slice_info = s
            break
    return {
        "redshift": z,
        "slice": slice_info,
        "comoving_distance_Mpc_h": round(d, 2),
        "cosmology": COSMO_PARAMS,
    }


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html><body style="background:#0a0a1a;color:#e0e0ff;font-family:monospace;padding:2em">
    <h1>🌌 The Universal Map (Omni-Chart)</h1>
    <p>API server running. Endpoints:</p>
    <ul>
        <li><a href="/api/v1/status" style="color:#88f">/api/v1/status</a></li>
        <li><a href="/api/v1/slices" style="color:#88f">/api/v1/slices</a></li>
        <li><a href="/api/v1/layer/l_gold" style="color:#88f">/api/v1/layer/l_gold</a></li>
        <li><a href="/api/v1/gold" style="color:#88f">/api/v1/gold</a></li>
        <li><a href="/api/v1/comoving_distance?z=1100" style="color:#88f">/api/v1/comoving_distance?z=1100</a></li>
        <li><a href="/api/v1/scrub_time?z=6" style="color:#88f">/api/v1/scrub_time?z=6</a></li>
    </ul>
    <p><em>Every zbit has a home.</em></p>
    </body></html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
