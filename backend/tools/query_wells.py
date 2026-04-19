"""Tool: Query wells by bbox, status, cluster from GeoJSON."""
import json
import os
from pathlib import Path

from models.schemas import WellInfo

DATA_DIR = os.environ.get("DATA_DIR", "./data")


def _load_wells() -> list[dict]:
    """Load wells from GeoJSON."""
    path = Path(DATA_DIR) / "wells.geojson"
    with open(path) as f:
        geojson = json.load(f)
    return geojson["features"]


def query_wells(
    bbox: list[float] | None = None,
    status: str | None = None,
    cluster_id: str | None = None,
) -> list[WellInfo]:
    """Query wells with optional filters."""
    features = _load_wells()
    results = []

    for feat in features:
        props = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]

        # Filter by bbox [west, south, east, north]
        if bbox is not None:
            west, south, east, north = bbox
            if not (west <= lon <= east and south <= lat <= north):
                continue

        # Filter by status
        if status is not None and props["status"] != status:
            continue

        # Filter by cluster
        if cluster_id is not None and props["cluster_id"] != cluster_id:
            continue

        results.append(WellInfo(
            id=props["id"],
            name=props["name_en"],
            cluster_id=props["cluster_id"],
            latitude=lat,
            longitude=lon,
            well_depth_m=props["well_depth_m"],
            aquifer_type=props["aquifer_type"],
            status=props["status"],
            current_yield_ls=props["current_yield_ls"],
            last_tds_mgl=props["last_tds_mgl"],
            last_ph=props["last_ph"],
            last_water_level_m=props["static_water_level_m"],
        ))

    return results
