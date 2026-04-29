"""Tool: Theis-based drawdown grid with isoline polygons."""
import json
import math
import os
from pathlib import Path

import numpy as np
from skimage import measure

from data_generator.hydro_models import theis_drawdown
from models.schemas import DrawdownGrid, DrawdownIsoline


ISOLINE_LEVELS = [0.5, 1.0, 2.0, 5.0]
DEFAULT_RESOLUTION = 50
DEFAULT_EXTENT_KM = 5


def _get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "./data")


def _load_wells() -> list[dict]:
    path = Path(_get_data_dir()) / "wells.geojson"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["features"]


def _km_to_deg_lat(km: float) -> float:
    return km / 111.0


def _km_to_deg_lon(km: float, lat_deg: float) -> float:
    return km / (111.0 * math.cos(math.radians(lat_deg)))


def _meters_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _is_edge_touching(contour: np.ndarray, n: int) -> bool:
    """True if any point of the contour lies on the outer grid boundary.

    Edge-touching contours are 'open' artefacts (the cone extends beyond the
    grid extent). Rendering them produces fake rectangular borders, so we drop
    them — better to show nothing than a misleading grid-aligned polygon.
    """
    eps = 0.5
    return bool(
        np.any(contour[:, 0] <= eps)
        or np.any(contour[:, 0] >= n - 1 - eps)
        or np.any(contour[:, 1] <= eps)
        or np.any(contour[:, 1] >= n - 1 - eps)
    )


def _contours_to_polygon(
    contours: list[np.ndarray],
    grid_lon: np.ndarray,
    grid_lat: np.ndarray,
) -> dict:
    """Convert scikit-image contour pixel coords to GeoJSON MultiPolygon."""
    multi_coords = []
    for c in contours:
        if len(c) < 3:
            continue
        ring = []
        for row, col in c:
            ri = int(round(row))
            ci = int(round(col))
            ri = max(0, min(grid_lat.shape[0] - 1, ri))
            ci = max(0, min(grid_lon.shape[0] - 1, ci))
            ring.append([float(grid_lon[ci]), float(grid_lat[ri])])
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        multi_coords.append([ring])

    return {"type": "MultiPolygon", "coordinates": multi_coords}


def compute_drawdown_grid(
    well_id: str,
    t_days: int = 30,
    extent_km: float = DEFAULT_EXTENT_KM,
    resolution: int = DEFAULT_RESOLUTION,
) -> DrawdownGrid:
    """
    Compute Theis drawdown on a square grid centered on well_id and return isoline polygons.

    Includes superposition from any other well within `extent_km`.
    """
    wells = _load_wells()
    target = next((w for w in wells if w["properties"]["id"] == well_id), None)
    if target is None:
        raise ValueError(f"Well not found: {well_id}")

    target_lon, target_lat = target["geometry"]["coordinates"]

    interfering = []
    relevant = [target]
    for w in wells:
        if w["properties"]["id"] == well_id:
            continue
        wlon, wlat = w["geometry"]["coordinates"]
        d = _meters_distance(target_lat, target_lon, wlat, wlon)
        if d <= extent_km * 1000 and w["properties"]["current_yield_ls"] > 0:
            interfering.append(w["properties"]["id"])
            relevant.append(w)

    d_lat = _km_to_deg_lat(extent_km)
    d_lon = _km_to_deg_lon(extent_km, target_lat)
    lats = np.linspace(target_lat - d_lat, target_lat + d_lat, resolution)
    lons = np.linspace(target_lon - d_lon, target_lon + d_lon, resolution)

    drawdown = np.zeros((resolution, resolution), dtype=float)
    for ri, lat in enumerate(lats):
        for ci, lon in enumerate(lons):
            total = 0.0
            for w in relevant:
                wlon, wlat = w["geometry"]["coordinates"]
                wp = w["properties"]
                q = wp["current_yield_ls"] * 86.4
                if q <= 0:
                    continue
                r = _meters_distance(lat, lon, wlat, wlon)
                r = max(r, 0.3)
                total += theis_drawdown(q, wp["transmissivity_m2d"], wp["storativity"], r, t_days)
            drawdown[ri, ci] = total

    max_dd = float(drawdown.max())

    isolines: list[DrawdownIsoline] = []
    for level in ISOLINE_LEVELS:
        if level >= max_dd:
            continue
        contours = measure.find_contours(drawdown, level)
        contours = [c for c in contours if not _is_edge_touching(c, resolution)]
        polygon = _contours_to_polygon(contours, lons, lats)
        if polygon["coordinates"]:
            isolines.append(DrawdownIsoline(level_m=level, polygon=polygon))

    return DrawdownGrid(
        well_id=well_id,
        center=[target_lon, target_lat],
        t_days=t_days,
        isolines=isolines,
        max_drawdown_m=round(max_dd, 2),
        interfering_wells=interfering,
    )
