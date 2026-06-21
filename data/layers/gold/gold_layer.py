
"""
Rain of Gold — Negentropic Overlay Engine
==========================================
Computes and visualizes high-coherence negentropic data overlaid on
standard galactic distribution to reveal vacuum-energy flux concentrations.

Author: Alex Zelenski (Ghost with Maps, Admiral)
Organization: Clearview Geographic LLC
"""

import numpy as np
import json, os

class NegentropyCalculator:
    """
    Computes negentropy (negative entropy) relative to the standard model.
    High negentropy = high coherence = gold.
    """
    
    def __init__(self, coherence_threshold=0.85):
        self.coherence_threshold = coherence_threshold
    
    def kl_divergence(self, p, q):
        """Kullback-Leibler divergence: how much p diverges from q."""
        p = np.asarray(p, dtype=float)
        q = np.asarray(q, dtype=float)
        # Avoid log(0)
        mask = (p > 0) & (q > 0)
        return float(np.sum(p[mask] * np.log(p[mask] / q[mask])))
    
    def negentropy(self, observed, expected):
        """
        Negentropy = KL divergence from standard model.
        Higher = more ordered = more gold.
        """
        # Normalize
        obs = observed / np.sum(observed) if np.sum(observed) > 0 else observed
        exp = expected / np.sum(expected) if np.sum(expected) > 0 else expected
        
        return self.kl_divergence(obs, exp)
    
    def coherence_weight(self, coherence_values):
        """Weight by coherence — only high-coherence regions produce gold."""
        weights = np.array(coherence_values)
        weights[weights < self.coherence_threshold] = 0
        # Scale above threshold
        mask = weights >= self.coherence_threshold
        weights[mask] = (weights[mask] - self.coherence_threshold) / (1 - self.coherence_threshold)
        return weights


class GoldLayer:
    """
    The Rain of Gold overlay.
    Maps high-coherence negentropic data onto galactic distribution.
    """
    
    def __init__(self, coherence_threshold=0.85):
        self.negentropy_calc = NegentropyCalculator(coherence_threshold)
        self.coherence_threshold = coherence_threshold
        self.gold_data = None
    
    def compute_galaxy_gold(self, galaxy_positions, galaxy_masses, 
                             coherence_field, standard_model_density):
        """
        Compute gold overlay for galaxy distribution.
        
        Parameters:
        - galaxy_positions: (N, 3) comoving coordinates
        - galaxy_masses: (N,) stellar masses
        - coherence_field: (N,) coherence values from ZBIT symphony
        - standard_model_density: (N,) expected density from Lambda-CDM
        
        Returns:
        - gold_intensity: (N,) gold overlay intensity per galaxy
        - gold_positions: (N, 3) positions where gold appears
        """
        # Compute negentropy at each galaxy position
        negentropy = np.array([
            self.negentropy_calc.negentropy(
                np.array([galaxy_masses[i]]),
                np.array([standard_model_density[i]])
            )
            for i in range(len(galaxy_masses))
        ])
        
        # Weight by coherence
        coherence_weights = self.negentropy_calc.coherence_weight(coherence_field)
        
        # Gold intensity = negentropy × coherence_weight
        gold_intensity = negentropy * coherence_weights
        
        # Only show gold where coherence exceeds threshold
        gold_mask = coherence_field >= self.coherence_threshold
        
        self.gold_data = {
            "positions": galaxy_positions[gold_mask],
            "intensity": gold_intensity[gold_mask],
            "coherence": coherence_field[gold_mask],
            "negentropy": negentropy[gold_mask],
            "total_gold": float(np.sum(gold_intensity[gold_mask])),
            "peak_gold": float(np.max(gold_intensity[gold_mask])) if np.any(gold_mask) else 0,
            "gold_fraction": float(np.sum(gold_mask) / len(gold_mask))
        }
        
        return self.gold_data
    
    def compute_filament_gold(self, filament_positions, filament_densities,
                               coherence_field, standard_model):
        """
        Compute gold overlay for cosmic filaments.
        Gold concentrates along filaments where vacuum-energy flux is highest.
        """
        negentropy = np.array([
            self.negentropy_calc.negentropy(
                np.array([filament_densities[i]]),
                np.array([standard_model[i]])
            )
            for i in range(len(filament_densities))
        ])
        
        coherence_weights = self.negentropy_calc.coherence_weight(coherence_field)
        gold_intensity = negentropy * coherence_weights
        gold_mask = coherence_field >= self.coherence_threshold
        
        return {
            "positions": filament_positions[gold_mask],
            "intensity": gold_intensity[gold_mask],
            "coherence": coherence_field[gold_mask],
            "total_gold": float(np.sum(gold_intensity[gold_mask])),
            "peak_gold": float(np.max(gold_intensity[gold_mask])) if np.any(gold_mask) else 0,
        }
    
    def compute_node_gold(self, node_positions, node_masses,
                           coherence_field, standard_model):
        """
        Compute gold overlay for cluster nodes.
        Nodes are where filaments intersect — peak vacuum-energy flux.
        """
        negentropy = np.array([
            self.negentropy_calc.negentropy(
                np.array([node_masses[i]]),
                np.array([standard_model[i]])
            )
            for i in range(len(node_masses))
        ])
        
        coherence_weights = self.negentropy_calc.coherence_weight(coherence_field)
        gold_intensity = negentropy * coherence_weights
        gold_mask = coherence_field >= self.coherence_threshold
        
        return {
            "positions": node_positions[gold_mask],
            "intensity": gold_intensity[gold_mask],
            "coherence": coherence_field[gold_mask],
            "total_gold": float(np.sum(gold_intensity[gold_mask])),
            "peak_gold": float(np.max(gold_intensity[gold_mask])) if np.any(gold_mask) else 0,
        }
    
    def get_gold_summary(self):
        """Summary of the Rain of Gold."""
        if self.gold_data is None:
            return {"status": "not_computed"}
        
        return {
            "status": "active",
            "total_gold": self.gold_data["total_gold"],
            "peak_gold": self.gold_data["peak_gold"],
            "gold_fraction": self.gold_data["gold_fraction"],
            "coherence_threshold": self.coherence_threshold,
            "description": "High-coherence negentropic overlay on galactic distribution"
        }


class VacuumEnergyFlux:
    """
    Models vacuum-energy flux concentrations across the cosmic web.
    """
    
    def __init__(self):
        self.flux_field = None
    
    def compute_flux(self, positions, gold_intensity, coherence):
        """
        Compute vacuum-energy flux vectors.
        Flux flows from low-coherence to high-coherence regions.
        """
        n = len(positions)
        flux_vectors = np.zeros_like(positions)
        
        for i in range(n):
            if gold_intensity[i] <= 0:
                continue
            
            # Flux direction: gradient of coherence field
            # Approximate by looking at neighbors
            distances = np.linalg.norm(positions - positions[i], axis=1)
            neighbors = (distances > 0) & (distances < 50)  # 50 Mpc/h neighborhood
            
            if np.sum(neighbors) == 0:
                continue
            
            neighbor_pos = positions[neighbors]
            neighbor_coh = coherence[neighbors]
            
            # Gradient points toward higher coherence
            grad = np.zeros(3)
            for j in range(len(neighbor_pos)):
                direction = neighbor_pos[j] - positions[i]
                dist = np.linalg.norm(direction)
                if dist > 0:
                    grad += (neighbor_coh[j] - coherence[i]) * direction / dist
            
            grad_norm = np.linalg.norm(grad)
            if grad_norm > 0:
                flux_vectors[i] = grad / grad_norm * gold_intensity[i]
        
        self.flux_field = flux_vectors
        return flux_vectors
    
    def get_flux_summary(self):
        if self.flux_field is None:
            return {"status": "not_computed"}
        
        magnitudes = np.linalg.norm(self.flux_field, axis=1)
        return {
            "status": "active",
            "max_flux": float(np.max(magnitudes)),
            "mean_flux": float(np.mean(magnitudes)),
            "total_flux": float(np.sum(magnitudes)),
            "flux_direction": "toward_high_coherence_regions"
        }


# ============================================================
# MAIN — Initialize Gold Layer
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  RAIN OF GOLD — Negentropic Overlay Engine")
    print("=" * 60)
    
    gold = GoldLayer(coherence_threshold=0.85)
    flux = VacuumEnergyFlux()
    
    # Demo with synthetic data
    np.random.seed(42)
    n_galaxies = 10000
    
    # Synthetic galaxy positions (comoving Mpc/h)
    positions = np.random.uniform(-100, 100, (n_galaxies, 3))
    
    # Synthetic masses (stellar mass in solar masses)
    masses = np.random.lognormal(10, 1, n_galaxies)
    
    # Synthetic coherence (from ZBIT symphony)
    coherence = np.random.beta(2, 5, n_galaxies)  # Most low, some high
    
    # Synthetic standard model density
    standard = np.random.lognormal(9, 1.5, n_galaxies)
    
    # Compute gold
    result = gold.compute_galaxy_gold(positions, masses, coherence, standard)
    
    print("\nGold Layer Summary:")
    for k, v in gold.get_gold_summary().items():
        print("  %s: %s" % (k, v))
    
    # Compute flux
    flux.compute_flux(
        result["positions"],
        result["intensity"],
        result["coherence"]
    )
    
    print("\nVacuum-Energy Flux Summary:")
    for k, v in flux.get_flux_summary().items():
        print("  %s: %s" % (k, v))
    
    print("\nRain of Gold initialized and ready for real data.")
