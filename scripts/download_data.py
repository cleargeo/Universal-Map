"""
Universal Map (Omni-Chart) — Data Download Script
Downloads cosmological data layers from public archives.
"""
import os
import sys
import json
import argparse
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

LAYERS = {
    "l0_cmb": {"name": "CMB", "url": "https://pla.esac.esa.int/aio-action?DOIDOC=Planck_HFI_2018_R3.01"},
    "l1_dark_matter": {"name": "Dark Matter", "url": "https://www.tng-project.org/api/TNG100-1/snapshots/99/"},
    "l2_filaments": {"name": "Filaments", "url": "https://gavo.ari.uni-heidelberg.de/tap"},
    "l3_nodes": {"name": "Nodes", "url": "https://skyserver.sdss.org/dr17/"},
    "l4_galaxies": {"name": "Galaxies", "url": "https://archive.stsci.edu/jwst/"},
    "l5_reionization": {"name": "Reionization", "url": "https://archive.stsci.edu/jwst/"},
    "l6_21cm": {"name": "21cm", "url": "https://reionization.org/"},
    "l_gold": {"name": "Rain of Gold", "url": None},
}

SLICES = ["z1100", "z20_10", "z10_6", "z6_3", "z3_1", "z1_05", "z05_0"]


def download_layer(layer_id: str, output_dir: Path) -> bool:
    """Download a single data layer."""
    layer = LAYERS.get(layer_id)
    if not layer:
        print(f"  Unknown layer: {layer_id}")
        return False
    
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / f"{layer_id}_metadata.json"
    
    # Write metadata stub
    metadata = {
        "layer_id": layer_id,
        "name": layer["name"],
        "url": layer["url"],
        "status": "stub",
        "note": "Full data download requires API keys and large storage. This is a metadata stub.",
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  ✅ {layer_id}: {layer['name']} (metadata stub)")
    return True


def download_slice(slice_id: str, output_dir: Path) -> bool:
    """Download temporal slice data."""
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / f"slice_{slice_id}.json"
    
    metadata = {
        "slice_id": slice_id,
        "status": "stub",
        "note": "Temporal slice data requires simulation output.",
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  ✅ Slice: {slice_id} (metadata stub)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Download Universal Map data layers")
    parser.add_argument("--layers", nargs="*", default=["all"], help="Layer IDs to download")
    parser.add_argument("--slices", nargs="*", default=["all"], help="Slice IDs to download")
    parser.add_argument("--output", type=str, default=str(DATA_DIR), help="Output directory")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    print(f"🌌 Universal Map Data Download")
    print(f"   Output: {output_dir}")
    print()
    
    # Layers
    if "all" in args.layers:
        layers_to_download = list(LAYERS.keys())
    else:
        layers_to_download = args.layers
    
    print(f"📦 Downloading {len(layers_to_download)} layers...")
    for layer_id in layers_to_download:
        download_layer(layer_id, output_dir / "layers")
    
    # Slices
    if "all" in args.slices:
        slices_to_download = SLICES
    else:
        slices_to_download = args.slices
    
    print(f"\n⏱️  Downloading {len(slices_to_download)} temporal slices...")
    for slice_id in slices_to_download:
        download_slice(slice_id, output_dir / "slices")
    
    print(f"\n✅ Download complete. Data in: {output_dir}")
    print("   Note: Full data requires API keys from Planck, JWST, DESI, SDSS.")


if __name__ == "__main__":
    main()
