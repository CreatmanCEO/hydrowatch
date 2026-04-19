"""Generate synthetic groundwater well GeoJSON for Abu Dhabi region."""
import json
import os
from pathlib import Path

import numpy as np

# Abu Dhabi well field clusters (center lat, lon, name)
CLUSTERS = [
    {"id": "AL_WATHBA", "name": "Al Wathba", "center": (24.42, 54.72), "radius_deg": 0.06},
    {"id": "MUSSAFAH", "name": "Mussafah Industrial", "center": (24.35, 54.50), "radius_deg": 0.04},
    {"id": "SWEIHAN", "name": "Sweihan", "center": (24.48, 55.35), "radius_deg": 0.08},
    {"id": "AL_KHATIM", "name": "Al Khatim", "center": (24.28, 55.10), "radius_deg": 0.07},
]

AQUIFER_TYPES = [
    {"name": "Dammam Limestone", "depth_range": (80, 200), "T_range": (200, 1200), "S_range": (0.002, 0.008)},
    {"name": "Umm Er Radhuma", "depth_range": (150, 350), "T_range": (100, 800), "S_range": (0.001, 0.005)},
    {"name": "Quaternary Sand", "depth_range": (30, 80), "T_range": (50, 400), "S_range": (0.01, 0.05)},
    {"name": "Alluvial", "depth_range": (20, 60), "T_range": (30, 300), "S_range": (0.05, 0.15)},
]

OPERATORS = [
    "ADNOC Water Resources",
    "Emirates Water & Electricity",
    "Al Ain Distribution Company",
    "Abu Dhabi Agriculture Authority",
]

STATUSES = ["active", "active", "active", "active", "inactive", "maintenance"]  # weighted


def generate_wells_geojson(
    n_wells: int = 25,
    n_clusters: int = 4,
    seed: int = 42,
) -> dict:
    """Generate a GeoJSON FeatureCollection of synthetic monitoring wells."""
    rng = np.random.default_rng(seed)
    clusters = CLUSTERS[:n_clusters]

    # Distribute wells across clusters
    wells_per_cluster = np.full(n_clusters, n_wells // n_clusters)
    remainder = n_wells % n_clusters
    for i in range(remainder):
        wells_per_cluster[i] += 1

    features = []
    well_idx = 0

    for ci, cluster in enumerate(clusters):
        for j in range(wells_per_cluster[ci]):
            well_idx += 1

            # Position: cluster center + random offset
            lat = cluster["center"][0] + rng.normal(0, cluster["radius_deg"] / 3)
            lon = cluster["center"][1] + rng.normal(0, cluster["radius_deg"] / 3)

            # Clamp to Abu Dhabi region
            lat = float(np.clip(lat, 24.05, 24.95))
            lon = float(np.clip(lon, 54.05, 55.95))

            # Select aquifer type
            aquifer = rng.choice(AQUIFER_TYPES)
            depth = float(rng.uniform(*aquifer["depth_range"]))
            T = float(rng.uniform(*aquifer["T_range"]))
            S = float(rng.uniform(*aquifer["S_range"]))

            # Hydrogeological parameters
            static_wl = float(rng.uniform(20, 80))
            yield_ls = float(rng.uniform(2, 30))
            tds = float(rng.uniform(2000, 8000))
            ph = float(rng.uniform(7.0, 8.5))
            chloride = float(rng.uniform(300, 5000))
            temp = float(rng.uniform(28, 38))
            ground_elev = float(rng.uniform(5, 120))
            casing_diam = int(rng.choice([150, 200, 250, 300]))

            status = str(rng.choice(STATUSES))
            operator = str(rng.choice(OPERATORS))
            install_year = int(rng.integers(1995, 2023))
            install_date = f"{install_year}-{rng.integers(1,13):02d}-{rng.integers(1,29):02d}"

            well_id = f"AUH-{ci+1:02d}-{j+1:03d}"
            name_en = f"{cluster['name']} Well {j+1}"

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lon, 6), round(lat, 6)],
                },
                "properties": {
                    "id": well_id,
                    "name_en": name_en,
                    "cluster_id": cluster["id"],
                    "cluster_name": cluster["name"],
                    "well_depth_m": round(depth, 1),
                    "aquifer_type": aquifer["name"],
                    "casing_diameter_mm": casing_diam,
                    "ground_elevation_m": round(ground_elev, 1),
                    "transmissivity_m2d": round(T, 1),
                    "storativity": round(S, 5),
                    "status": status,
                    "current_yield_ls": round(yield_ls, 2),
                    "static_water_level_m": round(static_wl, 1),
                    "last_tds_mgl": round(tds, 0),
                    "last_ph": round(ph, 2),
                    "last_chloride_mgl": round(chloride, 0),
                    "last_temperature_c": round(temp, 1),
                    "operator": operator,
                    "installation_date": install_date,
                },
            }
            features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def main():
    """Generate wells and save to data/wells.geojson."""
    geojson = generate_wells_geojson(n_wells=25, n_clusters=4)

    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    output_path = data_dir / "wells.geojson"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(geojson['features'])} wells -> {output_path.name}")


if __name__ == "__main__":
    main()
