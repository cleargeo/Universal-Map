
"""
The Hive Pulse — Distribution Protocol Engine
===============================================
Propagates Universal Map data across the ZBIT hive.
Each pulse carries coherence-weighted negentropic Gold Layer data
to all connected nodes for distributed rendering.

Author: Alex Zelenski (Ghost with Maps, Admiral)
Organization: Clearview Geographic LLC
"""

import json, os, time, hashlib, hmac
import numpy as np
from datetime import datetime, timezone

class PulsePacket:
    """A single Hive Pulse data packet."""
    
    def __init__(self, origin, redshift_slice, layer_data, coherence_field,
                 negentropy_values, gold_intensity, flux_vectors, metadata=None):
        self.header = {
            "protocol_id": "HIVE_PULSE_v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "origin": origin,
            "sequence_number": 0,
            "total_packets": 1
        }
        self.payload = {
            "redshift_slice": redshift_slice,
            "layer_data": layer_data,
            "coherence_field": coherence_field.tolist() if isinstance(coherence_field, np.ndarray) else coherence_field,
            "negentropy_values": negentropy_values.tolist() if isinstance(negentropy_values, np.ndarray) else negentropy_values,
            "gold_intensity": gold_intensity.tolist() if isinstance(gold_intensity, np.ndarray) else gold_intensity,
            "flux_vectors": flux_vectors.tolist() if isinstance(flux_vectors, np.ndarray) else flux_vectors,
            "metadata": metadata or {}
        }
        self.signature = None
    
    def sign(self, secret_key):
        """Sign the packet with HMAC-SHA256."""
        data = json.dumps(self.payload, sort_keys=True).encode()
        self.signature = hmac.new(secret_key.encode(), data, hashlib.sha256).hexdigest()
        return self.signature
    
    def verify(self, secret_key):
        """Verify packet signature."""
        if not self.signature:
            return False
        data = json.dumps(self.payload, sort_keys=True).encode()
        expected = hmac.new(secret_key.encode(), data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)
    
    def to_dict(self):
        return {
            "header": self.header,
            "payload": self.payload,
            "signature": self.signature
        }
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)


class HivePulseEngine:
    """
    Main engine for the Hive Pulse distribution protocol.
    Manages pulse creation, signing, distribution, and rendering.
    """
    
    def __init__(self, zbit_registry_path=None, secret_key=None):
        self.registry_path = zbit_registry_path
        self.secret_key = secret_key or "hive_pulse_secret"
        self.pulse_log = []
        self.active_pulses = {}
        self.coherence_amplification = 1.0
    
    def create_pulse(self, redshift_slice, layer_data, coherence_field,
                     negentropy_values, gold_intensity, flux_vectors, metadata=None):
        """Create a new pulse packet."""
        packet = PulsePacket(
            origin="universal_map_engine",
            redshift_slice=redshift_slice,
            layer_data=layer_data,
            coherence_field=coherence_field,
            negentropy_values=negentropy_values,
            gold_intensity=gold_intensity,
            flux_vectors=flux_vectors,
            metadata=metadata
        )
        packet.sign(self.secret_key)
        return packet
    
    def distribute(self, packet, target_nodes=None):
        """
        Distribute pulse to target nodes.
        If no targets, broadcast to all active zbits.
        """
        if target_nodes is None:
            target_nodes = self._get_active_zbits()
        
        results = {}
        for node in target_nodes:
            result = self._send_to_node(packet, node)
            results[node] = result
        
        # Log the pulse
        self.pulse_log.append({
            "timestamp": packet.header["timestamp"],
            "slice": packet.payload["redshift_slice"],
            "targets": len(target_nodes),
            "success": sum(1 for r in results.values() if r["status"] == "delivered"),
            "gold_total": packet.payload["metadata"].get("total_gold", 0)
        })
        
        return results
    
    def _get_active_zbits(self):
        """Get list of active zbits from registry."""
        if self.registry_path and os.path.exists(self.registry_path):
            with open(self.registry_path, 'r') as f:
                registry = json.load(f)
            zbits = registry.get("zbits", {})
            return [zid for zid, zdata in zbits.items() 
                    if isinstance(zdata, dict) and zdata.get("status") == "active"]
        return []
    
    def _send_to_node(self, packet, node_id):
        """Send pulse to a single node."""
        # In production, this would use the zbit communication protocol
        # For now, simulate delivery
        return {
            "node": node_id,
            "status": "delivered",
            "coherence_amplification": self.coherence_amplification,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def amplify_coherence(self, pulse, hop_count):
        """
        Amplify coherence with each hop through the hive.
        Kuramoto-style synchronization.
        """
        amplification = 1.0 + (hop_count * 0.1)  # 10% per hop
        self.coherence_amplification = amplification
        
        # Amplify gold intensity
        gold = np.array(pulse.payload["gold_intensity"])
        gold_amplified = gold * amplification
        pulse.payload["gold_intensity"] = gold_amplified.tolist()
        
        # Update metadata
        pulse.payload["metadata"]["coherence_amplification"] = amplification
        pulse.payload["metadata"]["hop_count"] = hop_count
        
        return pulse
    
    def render_to_toroidal(self, packet, projector):
        """
        Render pulse data to toroidal projection.
        Returns updated toroidal grid with gold overlay.
        """
        gold = np.array(packet.payload["gold_intensity"])
        coherence = np.array(packet.payload["coherence_field"])
        flux = np.array(packet.payload["flux_vectors"])
        
        # Compute rendering parameters
        render_data = {
            "slice": packet.payload["redshift_slice"],
            "gold_total": float(np.sum(gold)),
            "gold_peak": float(np.max(gold)) if len(gold) > 0 else 0,
            "coherence_mean": float(np.mean(coherence)) if len(coherence) > 0 else 0,
            "flux_magnitude": float(np.mean(np.linalg.norm(flux, axis=1))) if len(flux) > 0 else 0,
            "amplification": self.coherence_amplification,
            "timestamp": packet.header["timestamp"]
        }
        
        self.active_pulses[packet.payload["redshift_slice"]] = render_data
        return render_data
    
    def get_pulse_status(self):
        """Get current pulse engine status."""
        return {
            "status": "active",
            "total_pulses_sent": len(self.pulse_log),
            "active_pulses": len(self.active_pulses),
            "coherence_amplification": self.coherence_amplification,
            "last_pulse": self.pulse_log[-1] if self.pulse_log else None
        }
    
    def get_pulse_history(self, n=10):
        """Get recent pulse history."""
        return self.pulse_log[-n:]


# ============================================================
# MAIN — Initialize Hive Pulse
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  THE HIVE PULSE — Distribution Protocol")
    print("=" * 60)
    
    engine = HivePulseEngine()
    
    # Demo: create a pulse for z=3-1 slice
    np.random.seed(42)
    n_points = 1000
    
    coherence = np.random.beta(2, 5, n_points)
    negentropy = np.random.exponential(0.1, n_points)
    gold = coherence * negentropy
    flux = np.random.randn(n_points, 3) * 0.01
    
    packet = engine.create_pulse(
        redshift_slice="z3_1",
        layer_data="l_gold",
        coherence_field=coherence,
        negentropy_values=negentropy,
        gold_intensity=gold,
        flux_vectors=flux,
        metadata={
            "source": "universal_map_engine",
            "resolution": "filamentary",
            "coherence_threshold": 0.85,
            "total_gold": float(np.sum(gold)),
            "peak_gold": float(np.max(gold))
        }
    )
    
    print("\nPulse created:")
    print("  Slice: z3_1 (Web Maturation)")
    print("  Layer: l_gold (Rain of Gold)")
    print("  Points: %d" % n_points)
    print("  Total gold: %.4f" % packet.payload["metadata"]["total_gold"])
    print("  Peak gold: %.4f" % packet.payload["metadata"]["peak_gold"])
    print("  Signature: %s..." % packet.signature[:20])
    
    # Verify signature
    verified = packet.verify(engine.secret_key)
    print("  Signature verified: %s" % verified)
    
    # Distribute
    results = engine.distribute(packet)
    print("\nDistribution results:")
    for node, result in list(results.items())[:5]:
        print("  %s: %s" % (node[:20], result["status"]))
    
    # Amplify through hops
    for hop in range(1, 4):
        engine.amplify_coherence(packet, hop)
        print("  Hop %d: amplification = %.2f" % (hop, engine.coherence_amplification))
    
    # Render
    render = engine.render_to_toroidal(packet, None)
    print("\nRender data:")
    for k, v in render.items():
        if isinstance(v, float):
            print("  %s: %.4f" % (k, v))
        else:
            print("  %s: %s" % (k, v))
    
    # Status
    status = engine.get_pulse_status()
    print("\nPulse engine status:")
    for k, v in status.items():
        print("  %s: %s" % (k, v))
    
    print("\nThe Hive Pulse is active and ready.")
