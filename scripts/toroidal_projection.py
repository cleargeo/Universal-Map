
"""
Universal Map (Omni-Chart) — Toroidal Projection Engine
Maps the 3D cosmic web onto a toroidal surface for the ZBIT hive.
Integrates JWST and DESI redshift-distance slicing for temporal navigation.
Author: Alex Zelenski (Ghost with Maps, Admiral)
Organization: Clearview Geographic LLC
Version: 1.0.0
"""

import numpy as np
import json, os

COSMO_PARAMS = {
    "H0": 67.4, "Omega_m": 0.315, "Omega_lambda": 0.685,
    "Omega_b": 0.0493, "sigma_8": 0.811, "n_s": 0.965, "c": 299792.458,
}

class CosmologyEngine:
    def __init__(self, params=None):
        self.params = params or COSMO_PARAMS
        self.H0 = self.params["H0"]
        self.Omega_m = self.params["Omega_m"]
        self.Omega_lambda = self.params["Omega_lambda"]
        self.c = self.params["c"]
    
    def hubble_parameter(self, z):
        return self.H0 * np.sqrt(self.Omega_m * (1 + z)**3 + self.Omega_lambda)
    
    def comoving_distance(self, z, n_steps=1000):
        z_arr = np.linspace(0, z, n_steps)
        integrand = self.c / self.hubble_parameter(z_arr)
        return float(np.trapezoid(integrand, z_arr) / self.H0 * 100)
    
    def lookback_time(self, z, n_steps=1000):
        z_arr = np.linspace(0, z, n_steps)
        integrand = 1.0 / ((1 + z_arr) * self.hubble_parameter(z_arr))
        return float(np.trapezoid(integrand, z_arr) * 0.978 * 100 / self.H0)
    
    def age_of_universe(self, z, n_steps=1000):
        return self.lookback_time(1100) - self.lookback_time(z)

class ToroidalProjector:
    def __init__(self, R=1.0, r=0.3):
        self.R = R
        self.r = r
    
    def cartesian_to_toroidal(self, x, y, z):
        rho = np.sqrt(x**2 + y**2)
        phi = np.arctan2(y, x)
        d = np.sqrt((rho - self.R)**2 + z**2)
        theta = np.arctan2(z, rho - self.R)
        return theta, phi, d

class RedshiftSlicer:
    SLICES = [
        {"id": "z1100", "name": "Surface of Last Scattering", "z": 1100},
        {"id": "z20_10", "name": "Cosmic Dawn", "z_range": [20, 10]},
        {"id": "z10_6", "name": "Reionization", "z_range": [10, 6]},
        {"id": "z6_3", "name": "Galaxy Assembly", "z_range": [6, 3]},
        {"id": "z3_1", "name": "Web Maturation", "z_range": [3, 1]},
        {"id": "z1_0.5", "name": "Web Refinement", "z_range": [1, 0.5]},
        {"id": "z0.5_0", "name": "Present Expansion", "z_range": [0.5, 0]},
    ]
    
    def __init__(self, cosmology=None):
        self.cosmo = cosmology or CosmologyEngine()
    
    def get_slice(self, z):
        for s in self.SLICES:
            if "z" in s and z >= s["z"]:
                return s
            elif "z_range" in s and s["z_range"][0] >= z >= s["z_range"][1]:
                return s
        return self.SLICES[-1]

class UniversalMap:
    def __init__(self, config_path=None):
        self.cosmo = CosmologyEngine()
        self.projector = ToroidalProjector()
        self.slicer = RedshiftSlicer(self.cosmo)
        self.data = {}
        self.layers = {}
    
    def scrub_time(self, z):
        slice_info = self.slicer.get_slice(z)
        return {
            "redshift": z,
            "slice": slice_info,
            "comoving_distance_Mpc": self.cosmo.comoving_distance(z),
            "lookback_time_Gyr": self.cosmo.lookback_time(z),
            "age_of_universe_Gyr": self.cosmo.age_of_universe(z),
        }
    
    def get_status(self):
        return {
            "name": "The Universal Map (Omni-Chart)",
            "status": "active",
            "cosmology": "Planck 2018 Lambda-CDM",
            "projection": "toroidal",
            "layers_loaded": len(self.layers),
            "temporal_slices": len(self.slicer.SLICES),
            "redshift_range": [0, 1100],
        }

if __name__ == "__main__":
    print("=" * 60)
    print("  THE UNIVERSAL MAP (OMNI-CHART)")
    print("=" * 60)
    umap = UniversalMap()
    status = umap.get_status()
    for k, v in status.items():
        print("  %s: %s" % (k, v))
    print("\nTemporal Slices:")
    for s in umap.slicer.SLICES:
        z = s.get("z", s.get("z_range", "?"))
        print("  %-30s z=%s" % (s["name"], z))
    print("\nCosmological Distances:")
    for z in [0, 0.5, 1, 3, 6, 10, 1100]:
        d = umap.cosmo.comoving_distance(z)
        t = umap.cosmo.lookback_time(z)
        print("  z=%-6s  D_C=%-8.0f Mpc/h  t_lookback=%-6.2f Gyr" % (z, d, t))
    print("\nUniversal Map initialized and ready.")
