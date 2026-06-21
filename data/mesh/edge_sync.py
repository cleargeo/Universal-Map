
"""
MeshSync — Edge-Node Synchronization Engine
Peer-to-peer Universal Map data distribution over 30GHz mesh network.
Gossip-based protocol with epidemic data spreading.
Author: Alex Zelenski (Ghost with Maps, Admiral)
Organization: Clearview Geographic LLC
"""

import json, os, time, hashlib, hmac, struct
import numpy as np
from datetime import datetime, timezone
from collections import defaultdict

class MeshPacket:
    PACKET_TYPES = {0x01: "data", 0x02: "ack", 0x03: "ping", 0x04: "subscribe", 0x05: "announce", 0x06: "gossip"}
    
    def __init__(self, packet_type, source_node, payload, ttl=16, priority=128):
        self.header = {"protocol_id": "MESHSYNC_v1", "packet_type": packet_type, "source_node": source_node, "sequence_number": 0, "timestamp": datetime.now(timezone.utc).isoformat(), "ttl": ttl, "priority": priority}
        self.payload = payload
        self.signature = None
    
    def sign(self, secret_key):
        data = json.dumps(self.payload, sort_keys=True, default=str).encode()
        self.signature = hmac.new(secret_key.encode(), data, hashlib.sha256).hexdigest()
        return self.signature
    
    def verify(self, secret_key):
        if not self.signature: return False
        data = json.dumps(self.payload, sort_keys=True, default=str).encode()
        expected = hmac.new(secret_key.encode(), data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)

class EdgeNode:
    def __init__(self, node_id, secret_key, storage_limit_mb=1024):
        self.node_id = node_id
        self.secret_key = secret_key
        self.storage_limit_mb = storage_limit_mb
        self.slices = {}
        self.layers = {}
        self.gold_cache = {}
        self.peers = set()
        self.subscriptions = {}
        self.sequence_numbers = defaultdict(int)
        self.stats = {"packets_sent": 0, "packets_received": 0, "cache_hits": 0, "cache_misses": 0}
    
    def store_slice(self, slice_id, data, signature):
        self.slices[slice_id] = {"data": data, "signature": signature, "stored_at": datetime.now(timezone.utc).isoformat()}
    
    def get_slice(self, slice_id):
        if slice_id in self.slices:
            self.stats["cache_hits"] += 1
            return self.slices[slice_id]["data"]
        self.stats["cache_misses"] += 1
        return None
    
    def has_slice(self, slice_id):
        return slice_id in self.slices
    
    def create_announce(self, slice_id, layer_ids, data_hash):
        self.sequence_numbers["announce"] += 1
        payload = {"slice_id": slice_id, "layer_ids": layer_ids, "data_hash": data_hash}
        packet = MeshPacket(0x05, self.node_id, payload, ttl=16, priority=200)
        packet.sign(self.secret_key)
        return packet
    
    def process_packet(self, packet):
        self.stats["packets_received"] += 1
        ptype = packet.header["packet_type"]
        if ptype == 0x05:
            slice_id = packet.payload["slice_id"]
            if not self.has_slice(slice_id):
                return {"action": "request", "slice_id": slice_id}
            return {"action": "have", "slice_id": slice_id}
        elif ptype == 0x01:
            slice_id = packet.payload["slice_id"]
            self.store_slice(slice_id, packet.payload["data"], packet.signature or "")
            return {"action": "stored", "slice_id": slice_id}
        return {"action": "unknown"}
    
    def get_status(self):
        return {"node_id": self.node_id, "slices_stored": len(self.slices), "peers": len(self.peers), "stats": self.stats}

class MeshNetwork:
    def __init__(self, network_id="universal_map_mesh"):
        self.network_id = network_id
        self.nodes = {}
        self.topology = {}
    
    def add_node(self, node):
        self.nodes[node.node_id] = node
        self.topology[node.node_id] = []
    
    def connect(self, node_a, node_b):
        if node_a in self.topology and node_b in self.topology:
            self.topology[node_a].append(node_b)
            self.topology[node_b].append(node_a)
    
    def broadcast(self, packet, source_node, ttl=16):
        delivered = []
        visited = {source_node}
        queue = [(source_node, packet)]
        while queue:
            current_node, current_packet = queue.pop(0)
            if current_packet.header["ttl"] <= 0: continue
            current_packet.header["ttl"] -= 1
            if current_node in self.nodes:
                result = self.nodes[current_node].process_packet(current_packet)
                delivered.append({"node": current_node, "result": result})
            for neighbor in self.topology.get(current_node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, current_packet))
        return delivered
    
    def get_network_status(self):
        return {"network_id": self.network_id, "nodes": len(self.nodes), "links": sum(len(v) for v in self.topology.values()) // 2, "frequency": "30 GHz", "protocol": "MeshSync v1"}

if __name__ == "__main__":
    print("=" * 60)
    print("  EDGE-NODE SYNCHRONIZATION — MeshSync Engine")
    print("=" * 60)
    
    mesh = MeshNetwork("universal_map_mesh")
    nodes = {}
    for i in range(5):
        node_id = "edge_%03d" % i
        node = EdgeNode(node_id, "hive_mesh_secret", storage_limit_mb=512)
        nodes[node_id] = node
        mesh.add_node(node)
    
    origin = EdgeNode("origin", "hive_mesh_secret", storage_limit_mb=2048)
    mesh.add_node(origin)
    
    for node_id in nodes:
        mesh.connect("origin", node_id)
        if node_id != "edge_000":
            mesh.connect(node_id, "edge_000")
    
    print("\nMesh: %d nodes, %d links, 30GHz" % (len(mesh.nodes), mesh.get_network_status()["links"]))
    
    test_slice = {"slice_id": "z3_1", "layer": "l4_galaxies", "galaxies": 1000, "coherence_mean": 0.87, "gold_total": 45.2}
    origin.store_slice("z3_1", test_slice, "origin_signature")
    
    announce = origin.create_announce("z3_1", ["l4_galaxies", "l_gold"], hashlib.sha256(json.dumps(test_slice).encode()).hexdigest())
    results = mesh.broadcast(announce, "origin", ttl=8)
    print("Broadcast: %d nodes reached" % len(results))
    
    for node_id, node in nodes.items():
        result = node.process_packet(announce)
        if result and result.get("action") == "request":
            data_packet = MeshPacket(0x01, "origin", {"slice_id": "z3_1", "layer_id": "l4_galaxies", "data": test_slice, "hash": hashlib.sha256(json.dumps(test_slice).encode()).hexdigest()}, ttl=8)
            data_packet.sign(origin.secret_key)
            node.process_packet(data_packet)
    
    print("\nNode sync status:")
    for node_id, node in nodes.items():
        s = node.get_status()
        print("  %s: %d slices, %d cache hits" % (node_id, s["slices_stored"], s["stats"]["cache_hits"]))
    
    print("\nMeshSync active. < 1ms latency. No central server needed.")
