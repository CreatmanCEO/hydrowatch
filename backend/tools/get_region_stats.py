"""Tool: Aggregate statistics for wells in a bounding box."""
import json
import os
from pathlib import Path

import numpy as np

from models.schemas import RegionStats

DATA_DIR = os.environ.get("DATA_DIR", "./data")


def get_region_stats(
    bbox: list[float],
) -> RegionStats:
    """Aggregate stats for wells within bbox [west, south, east, north]."""
    path = Path(DATA_DIR) / "wells.geojson"
    with open(path) as f:
        geojson = json.load(f)

    west, south, east, north = bbox
    wells_in_bbox = []
    active_count = 0
    debits = []
    tds_values = []

    for feat in geojson["features"]:
        props = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]

        if west <= lon <= east and south <= lat <= north:
            wells_in_bbox.append(props["id"])
            if props["status"] == "active":
                active_count += 1
            debits.append(props["current_yield_ls"])
            tds_values.append(props["last_tds_mgl"])

    return RegionStats(
        well_count=len(wells_in_bbox),
        active_count=active_count,
        avg_debit_ls=round(float(np.mean(debits)), 2) if debits else 0.0,
        avg_tds_mgl=round(float(np.mean(tds_values)), 1) if tds_values else 0.0,
        anomaly_count=0,  # populated later by anomaly detector
        wells_in_bbox=wells_in_bbox,
    )
