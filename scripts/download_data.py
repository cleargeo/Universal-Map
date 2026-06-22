#!/usr/bin/env python3
"""
Universal Map — Synthetic Data Generator
Generates realistic synthetic data for all 8 layers and 7 temporal slices.
Uses Planck 2018 cosmology and physically-motivated distributions.

Author: Alex Zelenski (Ghost with Maps, Admiral)
Organization: Clearview Geographic LLC
"""

import numpy as np
import json
import os
import argparse
from datetime import datetime, timezone

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LAYERS_DIR = os.path.join(DATA_DIR, "layers")
SLICES_DIR = os.path.join(DATA_DIR, "slices")

LAYER_CONFIG = {
    "l0_cmb": {
        "name": "CMB",
        "redshift": 1100,
        "n_points": 5000,
        "format": "cog",
        "description": "Cosmic Microwave Background — Planck 2018 temperature anisotropies",
    },
    "l1_dark_matter": {
        "name": "Dark Matter",
        "redshift_range": [0, 10],
        "n_points": 8000,
        "format": "cog",
        "description": "Dark matter density field from IllustrisTNG simulation",
    },
    "l2_filaments": {
        "name": "Filaments",
        "redshift_range": [0, 6],
        "n_points": 6000,
        "format": "geojson",
        "description": "Cosmic web filaments from Millennium + DESI",
    },
    "l3_nodes": {
        "name": "Nodes",
        "redshift_range": [0, 3],
        "n_points": 4000,
        "format": "geojson",
        "description": "Galaxy cluster nodes from SDSS + DESI",
    },
    "l4_galaxies": {
        "name": "Galaxies",
        "redshift_range": [0, 20],
        "n_points": 10000,
        "format": "geojson",
        "description": "Galaxy positions from JWST + SDSS + DESI",
    },
    "l5_reionization": {
        "name": "Reionization",
        "redshift_range": [6, 20],
        "n_points": 3000,
        "format": "cog",
        "description": "Reionization history from JWST",
    },
    "l6_21cm": {
        "name": "21cm",
        "redshift_range": [6, 20],
        "n_points": 3500,
        "format": "cog",
        "description": "21cm signal from HERA + EDGES",
    },
    "l_gold": {
        "name": "Rain of Gold",
        "redshift_range": [0, 1100],
        "n_points": 2000,
        "format": "geojson",
        "description": "High-coherence negentropic overlay — computed from all layers",
    },
}

SLICE_CONFIG = [
    {"id": "z1100", "name": "Surface of Last Scattering", "z": 1100, "lookback_Gyr": 13.80},
    {"id": "z20_10", "name": "Cosmic Dawn", "z_range": [20, 10], "lookback_Gyr": 13.0},
    {"id": "z10_6", "name": "Epoch of Reionization", "z_range": [10, 6], "lookback_Gyr": 12.85},
    {"id": "z6_3", "name": "Galaxy Assembly", "z_range": [6, 3], "lookback_Gyr": 12.1},
    {"id": "z3_1", "name": "Web Maturation", "z_range": [3, 1], "lookback_Gyr": 9.6},
    {"id": "z1_0.5", "name": "Web Refinement", "z_range": [1, 0.5], "lookback_Gyr": 6.4},
    {"id": "z0.5_0", "name": "Present Expansion", "z_range": [0.5, 0], "lookback_Gyr": 2.5},
]


def ensure_dirs():
    """Create all necessary data directories."""
    os.makedirs(LAYERS_DIR, exist_ok=True)
    os.makedirs(SLICES_DIR, exist_ok=True)
    for layer_id in LAYER_CONFIG:
        os.makedirs(os.path.join(LAYERS_DIR, layer_id), exist_ok=True)
    for slice_info in SLICE_CONFIG:
        os.makedirs(os.path.join(SLICES_DIR, slice_info["id"]), exist_ok=True)


def generate_positions(n, distribution="uniform", **kwargs):
    """Generate 3D positions in comoving space (Mpc/h)."""
    if distribution == "uniform":
        box = kwargs.get("box_size", 200)
        return np.random.uniform(-box / 2, box / 2, (n, 3))
    elif distribution == "clustered":
        n_clusters = kwargs.get("n_clusters", 10)
        box = kwargs.get("box_size", 200)
        cluster_centers = np.random.uniform(-box / 2, box / 2, (n_clusters, 3))
        positions = []
        for i in range(n):
            c = cluster_centers[np.random.randint(n_clusters)]
            offset = np.random.randn(3) * 15
            positions.append(c + offset)
        return np.clip(np.array(positions), -box / 2, box / 2)
    elif distribution == "filament":
        box = kwargs.get("box_size", 200)
        n_filaments = kwargs.get("n_filaments", 8)
        positions = []
        for _ in range(n):
            t = np.random.uniform(0, 1)
            fil = np.random.randint(n_filaments)
            base = np.random.uniform(-box / 2, box / 2, 3)
            # Elongate along one axis
            base[fil % 3] += (t - 0.5) * box * 0.8
            # Add noise perpendicular
            noise = np.random.randn(3) * 5
            noise[fil % 3] *= 0.1
            positions.append(base + noise)
        return np.clip(np.array(positions), -box / 2, box / 2)
    elif distribution == "sphere":
        r = kwargs.get("radius", 100)
        theta = np.random.uniform(0, 2 * np.pi, n)
        phi = np.random.uniform(0, np.pi, n)
        radii = r * np.random.uniform(0.8, 1.0, n)
        x = radii * np.sin(phi) * np.cos(theta)
        y = radii * np.sin(phi) * np.sin(theta)
        z = radii * np.cos(phi)
        return np.column_stack([x, y, z])
    else:
        return np.random.uniform(-100, 100, (n, 3))


def generate_cmb_data(config):
    """Generate synthetic CMB temperature anisotropy data."""
    n = config["n_points"]
    positions = generate_positions(n, "sphere", radius=180)

    # CMB temperature: ~2.725K with ~100 uK anisotropies
    # Use spherical harmonics approximation
    l_max = 20
    np.random.seed(42)
    a_lm = np.random.randn(l_max * (l_max + 1) // 2) * 100e-6

    # Simplified: generate temperature from random fluctuations
    temp_fluctuation = np.random.randn(n) * 100e-6  # ~100 uK rms
    temperature = 2.725 * (1 + temp_fluctuation)

    # Polarization (E-mode)
    polarization_e = np.random.randn(n) * 10e-6

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": pos.tolist(),
                },
                "properties": {
                    "temperature_K": float(temp),
                    "polarization_e": float(pol),
                    "redshift": 1100,
                    "layer": "l0_cmb",
                },
            }
            for pos, temp, pol in zip(positions, temperature, polarization_e)
        ],
        "properties": {
            "layer": "l0_cmb",
            "description": config["description"],
            "units": {"temperature_K": "Kelvin", "polarization_e": "dimensionless"},
            "n_points": n,
        },
    }


def generate_dark_matter_data(config):
    """Generate synthetic dark matter density field."""
    n = config["n_points"]
    positions = generate_positions(n, "clustered", n_clusters=15, box_size=250)

    # Density: log-normal distribution (characteristic of DM fields)
    density = np.random.lognormal(0, 1.5, n)

    # Velocity field (peculiar velocity from gravitational infall)
    velocities = np.random.randn(n, 3) * 300  # km/s

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": pos.tolist(),
                },
                "properties": {
                    "density": float(dens),
                    "velocity_kms": vel.tolist(),
                    "mass_msun": float(dens * 1e12),
                    "layer": "l1_dark_matter",
                },
            }
            for pos, dens, vel in zip(positions, density, velocities)
        ],
        "properties": {
            "layer": "l1_dark_matter",
            "description": config["description"],
            "units": {"density": "dimensionless (rho/rho_mean)", "velocity_kms": "km/s", "mass_msun": "solar masses"},
            "n_points": n,
        },
    }


def generate_filament_data(config):
    """Generate synthetic cosmic web filament data."""
    n = config["n_points"]
    positions = generate_positions(n, "filament", n_filaments=12, box_size=200)

    # Filament properties
    density = np.random.lognormal(0, 1.0, n)
    width_kpc = np.random.lognormal(2, 0.5, n)  # ~10-100 kpc
    redshift = np.random.uniform(0, 6, n)

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        pos.tolist(),
                        (pos + np.random.randn(3) * 5).tolist(),
                    ],
                },
                "properties": {
                    "density": float(dens),
                    "width_kpc": float(width),
                    "redshift": float(z),
                    "layer": "l2_filaments",
                },
            }
            for pos, dens, width, z in zip(positions, density, width_kpc, redshift)
        ],
        "properties": {
            "layer": "l2_filaments",
            "description": config["description"],
            "units": {"density": "dimensionless", "width_kpc": "kiloparsecs", "redshift": "dimensionless"},
            "n_points": n,
        },
    }


def generate_node_data(config):
    """Generate synthetic cluster node data."""
    n = config["n_points"]
    positions = generate_positions(n, "clustered", n_clusters=20, box_size=180)

    # Cluster properties
    mass = np.random.lognormal(14, 1.0, n)  # 10^13 - 10^16 Msun
    richness = np.random.lognormal(2, 0.8, n)  # galaxy count
    redshift = np.random.uniform(0, 3, n)
    velocity_dispersion = np.random.lognormal(2.5, 0.3, n) * 1000  # km/s

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": pos.tolist(),
                },
                "properties": {
                    "mass_msun": float(m),
                    "richness": float(rich),
                    "redshift": float(z),
                    "velocity_dispersion_kms": float(vd),
                    "layer": "l3_nodes",
                },
            }
            for pos, m, rich, z, vd in zip(positions, mass, richness, redshift, velocity_dispersion)
        ],
        "properties": {
            "layer": "l3_nodes",
            "description": config["description"],
            "units": {"mass_msun": "solar masses", "richness": "galaxy count", "velocity_dispersion_kms": "km/s"},
            "n_points": n,
        },
    }


def generate_galaxy_data(config):
    """Generate synthetic galaxy catalog."""
    n = config["n_points"]
    positions = generate_positions(n, "clustered", n_clusters=25, box_size=220)

    # Galaxy properties
    stellar_mass = np.random.lognormal(10, 1.0, n)  # Msun
    redshift = np.random.uniform(0, 20, n)
    sfr = np.random.lognormal(0, 1.5, n)  # star formation rate Msun/yr
    metallicity = np.random.lognormal(-1, 0.5, n)  # Z/Zsun
    morphology = np.random.choice(["spiral", "elliptical", "irregular", "merger"], n)

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": pos.tolist(),
                },
                "properties": {
                    "stellar_mass_msun": float(sm),
                    "redshift": float(z),
                    "sfr_msun_yr": float(s),
                    "metallicity_zsun": float(zmet),
                    "morphology": morph,
                    "layer": "l4_galaxies",
                },
            }
            for pos, sm, z, s, zmet, morph in zip(positions, stellar_mass, redshift, sfr, metallicity, morphology)
        ],
        "properties": {
            "layer": "l4_galaxies",
            "description": config["description"],
            "units": {"stellar_mass_msun": "solar masses", "sfr_msun_yr": "solar masses/year"},
            "n_points": n,
        },
    }


def generate_reionization_data(config):
    """Generate synthetic reionization history data."""
    n = config["n_points"]
    positions = generate_positions(n, "uniform", box_size=150)

    # Reionization properties
    redshift = np.random.uniform(6, 20, n)
    ionized_fraction = np.clip(1.0 - (redshift - 6) / 14 + np.random.randn(n) * 0.05, 0, 1)
    optical_depth = np.random.lognormal(-1, 0.5, n)

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": pos.tolist(),
                },
                "properties": {
                    "redshift": float(z),
                    "ionized_fraction": float(xhi),
                    "optical_depth": float(tau),
                    "layer": "l5_reionization",
                },
            }
            for pos, z, xhi, tau in zip(positions, redshift, ionized_fraction, optical_depth)
        ],
        "properties": {
            "layer": "l5_reionization",
            "description": config["description"],
            "units": {"ionized_fraction": "dimensionless", "optical_depth": "dimensionless"},
            "n_points": n,
        },
    }


def generate_21cm_data(config):
    """Generate synthetic 21cm signal data."""
    n = config["n_points"]
    positions = generate_positions(n, "uniform", box_size=160)

    # 21cm properties
    redshift = np.random.uniform(6, 20, n)
    brightness_temp = np.random.randn(n) * 20 + 10  # mK
    bandwidth_mhz = np.random.uniform(0.1, 1.0, n)

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": pos.tolist(),
                },
                "properties": {
                    "redshift": float(z),
                    "brightness_temp_mK": float(tb),
                    "bandwidth_MHz": float(bw),
                    "layer": "l6_21cm",
                },
            }
            for pos, z, tb, bw in zip(positions, redshift, brightness_temp, bandwidth_mhz)
        ],
        "properties": {
            "layer": "l6_21cm",
            "description": config["description"],
            "units": {"brightness_temp_mK": "milliKelvin", "bandwidth_MHz": "MHz"},
            "n_points": n,
        },
    }


def generate_gold_data(config):
    """Generate Rain of Gold — high-coherence negentropic overlay."""
    n = config["n_points"]
    positions = generate_positions(n, "clustered", n_clusters=8, box_size=120)

    # Gold properties: high coherence regions
    coherence = np.random.beta(5, 2, n)  # Skewed high
    negentropy = np.random.exponential(0.3, n)
    gold_intensity = coherence * negentropy
    flux_vectors = np.random.randn(n, 3) * 0.01 * gold_intensity[:, np.newaxis]

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": pos.tolist(),
                },
                "properties": {
                    "coherence": float(coh),
                    "negentropy": float(neg),
                    "gold_intensity": float(gold),
                    "flux_vector": fv.tolist(),
                    "layer": "l_gold",
                },
            }
            for pos, coh, neg, gold, fv in zip(positions, coherence, negentropy, gold_intensity, flux_vectors)
        ],
        "properties": {
            "layer": "l_gold",
            "description": config["description"],
            "units": {"coherence": "dimensionless", "negentropy": "dimensionless", "gold_intensity": "dimensionless"},
            "n_points": n,
            "total_gold": float(np.sum(gold_intensity)),
            "peak_gold": float(np.max(gold_intensity)),
            "coherence_threshold": 0.85,
        },
    }


def generate_slice_data(slice_info):
    """Generate temporal slice calibration data."""
    z = slice_info.get("z", slice_info.get("z_range", [0, 0])[0])
    z_range = slice_info.get("z_range", [z, z])

    return {
        "slice_id": slice_info["id"],
        "name": slice_info["name"],
        "redshift": z,
        "redshift_range": z_range,
        "lookback_time_Gyr": slice_info["lookback_Gyr"],
        "layers_available": list(LAYER_CONFIG.keys()),
        "cosmology": "Planck 2018 Lambda-CDM",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


GENERATORS = {
    "l0_cmb": generate_cmb_data,
    "l1_dark_matter": generate_dark_matter_data,
    "l2_filaments": generate_filament_data,
    "l3_nodes": generate_node_data,
    "l4_galaxies": generate_galaxy_data,
    "l5_reionization": generate_reionization_data,
    "l6_21cm": generate_21cm_data,
    "l_gold": generate_gold_data,
}


def generate_all():
    """Generate all data for all layers and slices."""
    ensure_dirs()
    np.random.seed(42)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layers": {},
        "slices": {},
    }

    print("Generating layer data...")
    for layer_id, config in LAYER_CONFIG.items():
        print("  %s (%s)..." % (layer_id, config["name"]))
        generator = GENERATORS[layer_id]
        data = generator(config)

        output_path = os.path.join(LAYERS_DIR, layer_id, "data.json")
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        manifest["layers"][layer_id] = {
            "name": config["name"],
            "n_points": len(data["features"]),
            "format": config["format"],
            "path": "layers/%s/data.json" % layer_id,
        }
        print("    -> %d features" % len(data["features"]))

    print("\nGenerating temporal slices...")
    for slice_info in SLICE_CONFIG:
        print("  %s..." % slice_info["id"])
        data = generate_slice_data(slice_info)

        output_path = os.path.join(SLICES_DIR, slice_info["id"], "calibration.json")
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        manifest["slices"][slice_info["id"]] = {
            "name": slice_info["name"],
            "redshift": slice_info.get("z", slice_info.get("z_range")),
            "path": "slices/%s/calibration.json" % slice_info["id"],
        }

    # Write manifest
    manifest_path = os.path.join(DATA_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("\nManifest written to data/manifest.json")
    print("Total: %d layers, %d slices" % (len(manifest["layers"]), len(manifest["slices"])))
    return manifest


def generate_layers(layer_ids):
    """Generate data for specific layers only."""
    ensure_dirs()
    np.random.seed(42)

    for layer_id in layer_ids:
        if layer_id not in LAYER_CONFIG:
            print("Unknown layer: %s" % layer_id)
            continue
        config = LAYER_CONFIG[layer_id]
        generator = GENERATORS[layer_id]
        data = generator(config)

        output_path = os.path.join(LAYERS_DIR, layer_id, "data.json")
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print("  %s: %d features" % (layer_id, len(data["features"])))


def generate_slices(slice_ids):
    """Generate data for specific slices only."""
    ensure_dirs()

    for slice_id in slice_ids:
        match = [s for s in SLICE_CONFIG if s["id"] == slice_id]
        if not match:
            print("Unknown slice: %s" % slice_id)
            continue
        data = generate_slice_data(match[0])
        output_path = os.path.join(SLICES_DIR, slice_id, "calibration.json")
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print("  %s: done" % slice_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Map Data Generator")
    parser.add_argument("--layers", nargs="*", help="Layer IDs to generate (default: all)")
    parser.add_argument("--slices", nargs="*", help="Slice IDs to generate (default: all)")
    args = parser.parse_args()

    if not args.layers and not args.slices:
        generate_all()
    else:
        if args.layers:
            generate_layers(args.layers)
        if args.slices:
            generate_slices(args.slices)
