# The Universal Map (Omni-Chart)

> A dynamic, multi-layered toroidal reconstruction of the universe's large-scale structure, mapping down to filamentary dark matter structures across 13.8 billion years of cosmic evolution.

![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-blue)
![Standards](https://img.shields.io/badge/standards-FAIR%20%7C%20STAC%20%7C%20GeoJSON%20%7C%20COG-green)

## Overview

The Universal Map is an open-source cosmological visualization framework that maps the cosmic web — the large-scale structure of the universe — onto a toroidal surface. It integrates observational data from JWST, DESI, Planck, and SDSS with simulation data from IllustrisTNG and the Millennium Simulation.

### Key Features

- **8 Data Layers**: CMB → Dark Matter → Filaments → Nodes → Galaxies → Reionization → 21cm → Rain of Gold
- **7 Temporal Slices**: Redshift-distance calibrated from z=1100 to z=0 (13.8 billion years)
- **Toroidal Projection**: 3D cosmic web mapped to a navigable toroidal surface
- **Rain of Gold**: High-coherence negentropic overlay revealing vacuum-energy flux concentrations
- **Hive Pulse**: Real-time distribution protocol for decentralized nodes
- **Direct-to-Network Broadcast**: REST API, WebSocket, IPFS, Trinity Relay, Armada

## FAIR Principles

- **Findable**: STAC-compliant metadata, DOI-ready, searchable via standard catalogs
- **Accessible**: Open APIs (REST, WebSocket, IPFS), multiple download formats
- **Interoperable**: GeoJSON, Cloud-Optimized GeoTIFF (COG), STAC, ISO 19115 metadata
- **Reusable**: MIT license, documented schemas, reproducible pipelines

## Data Layers

| Layer | ID | Redshift Range | Data Source | Format |
|-------|----|----------------|-------------|--------|
| CMB | l0_cmb | z~1100 | Planck 2018 | COG + GeoJSON |
| Dark Matter | l1_dark_matter | z=0-10 | IllustrisTNG | COG + HDF5 |
| Filaments | l2_filaments | z=0-6 | Millennium + DESI | GeoJSON + GraphML |
| Nodes | l3_nodes | z=0-3 | SDSS + DESI | GeoJSON |
| Galaxies | l4_galaxies | z=0-20 | JWST + SDSS + DESI | GeoJSON + FITS |
| Reionization | l5_reionization | z=6-20 | JWST | COG |
| 21cm | l6_21cm | z=6-20 | HERA + EDGES | COG |
| Rain of Gold | l_gold | z=0-1100 | Computed | GeoJSON + Custom |

## Temporal Slices

| Slice | Redshift | Lookback Time | Age of Universe |
|-------|----------|---------------|-----------------|
| Surface of Last Scattering | z=1100 | 13.80 Gyr | 0.00038 Gyr |
| Cosmic Dawn | z=20-10 | 13.3-13.0 Gyr | 0.2-0.5 Gyr |
| Epoch of Reionization | z=10-6 | 13.0-12.7 Gyr | 0.5-0.9 Gyr |
| Galaxy Assembly | z=6-3 | 12.7-11.5 Gyr | 0.9-2.2 Gyr |
| Web Maturation | z=3-1 | 11.5-7.7 Gyr | 2.2-6.0 Gyr |
| Web Refinement | z=1-0.5 | 7.7-5.1 Gyr | 6.0-8.7 Gyr |
| Present Expansion | z=0.5-0 | 5.1-0 Gyr | 8.7-13.8 Gyr |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/cleargeo/Universal-Map.git
cd Universal-Map

# Install dependencies (recommended: use uv)
uv venv .venv --python 3.12
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux
uv pip install numpy scipy pandas matplotlib astropy astroquery geopandas shapely pyproj rasterio xarray rioxarray plotly bokeh h5py netCDF4 zarr fastapi uvicorn websockets pystac stac-asset colossus requests tqdm pyyaml

# Or using pip (Windows: nbodykit and healpy are disabled)
pip install -r requirements.txt

# Run the toroidal projection demo
python scripts/toroidal_projection.py

# Download data (requires full dependencies)
python scripts/download_data.py --layers all --slices all

# Launch interactive visualization
python scripts/visualize.py --mode toroidal --layer gold

# Start API server
python scripts/api.py --port 8080
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/slices` | GET | List available temporal slices |
| `/api/v1/layer/{id}` | GET | Get layer metadata |
| `/api/v1/layer/{id}/data` | GET | Get layer data (GeoJSON) |
| `/api/v1/gold` | GET | Get Gold Layer overlay |
| `/api/v1/flux` | GET | Get vacuum-energy flux vectors |
| `/api/v1/pulse` | GET | Get Hive Pulse status |
| `/api/v1/pulse/stream` | SSE | Real-time pulse stream |
| `/ws` | WebSocket | Real-time updates |

## Data Formats

- **GeoJSON** (RFC 7946): Point, LineString, Polygon features for all spatial data
- **Cloud-Optimized GeoTIFF** (COG): Raster data (CMB, dark matter density, 21cm)
- **STAC** (SpatioTemporal Asset Catalog): Metadata catalog for all layers
- **ISO 19115**: Geographic information metadata standard
- **HDF5**: Large simulation datasets
- **FITS**: Astronomical data standard

## Citation

```bibtex
@software{universal_map_2026,
  author = {Zelenski, Alex},
  title = {The Universal Map (Omni-Chart)},
  year = {2026},
  publisher = {Clearview Geographic LLC},
  url = {https://github.com/cleargeo/Universal-Map},
  license = {MIT}
}
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- Planck Collaboration (CMB data)
- JWST Science Teams (high-redshift observations)
- DESI Collaboration (spectroscopic survey)
- IllustrisTNG Team (simulation data)
- SDSS Collaboration (galaxy catalogs)
- Millennium Simulation Team (N-body data)

---

*Environmental stewardship through geospatial intelligence. Every zbit has a home.*
