"""Tool: Theis-based interference analysis between well pairs."""
import json
import math
import os
from pathlib import Path

from data_generator.hydro_models import theis_drawdown
from models.schemas import InterferencePair, InterferenceResult


def _get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "./data")


def _wgs84_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _severity_from_coef(c_max: float) -> str:
    if c_max >= 0.60:
        return "critical"
    if c_max >= 0.40:
        return "high"
    if c_max >= 0.20:
        return "medium"
    return "low"


def _recommendation(severity: str, dominant: str, victim: str, distance_km: float) -> str:
    if severity == "critical":
        return (
            f"URGENT: Reduce pumping at {dominant} or relocate {victim} "
            f"to >2km away. Current spacing {distance_km:.2f}km creates severe interference."
        )
    if severity == "high":
        return (
            f"Schedule pump test at {dominant} and {victim}. "
            f"Consider staggered pumping schedule to reduce simultaneous load."
        )
    if severity == "medium":
        return (
            f"Monitor combined drawdown at {dominant}-{victim} pair. "
            f"Acceptable but watch for further decline."
        )
    return f"Routine monitoring sufficient for {dominant}-{victim} pair."


def analyze_interference(
    bbox: list[float] | None = None,
    t_days: int = 30,
    min_coefficient: float = 0.10,
) -> InterferenceResult:
    """
    Compute Theis-based interference for all well pairs in bbox.

    Args:
        bbox: [west, south, east, north] WGS84. None = all wells.
        t_days: pumping time horizon (days).
        min_coefficient: filter out pairs with max coef below this threshold.

    Returns:
        InterferenceResult with significant pairs.
    """
    geojson_path = Path(_get_data_dir()) / "wells.geojson"
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    wells_in_bbox = []
    for feat in geojson["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        if bbox is not None:
            west, south, east, north = bbox
            if not (west <= lon <= east and south <= lat <= north):
                continue
        wells_in_bbox.append(feat)

    pairs: list[InterferencePair] = []
    well_radius_m = 0.3

    for i in range(len(wells_in_bbox)):
        for j in range(i + 1, len(wells_in_bbox)):
            a, b = wells_in_bbox[i], wells_in_bbox[j]
            pa, pb = a["properties"], b["properties"]
            lon_a, lat_a = a["geometry"]["coordinates"]
            lon_b, lat_b = b["geometry"]["coordinates"]

            r = _wgs84_distance_m(lat_a, lon_a, lat_b, lon_b)
            if r < 1.0:
                continue

            q_a = pa["current_yield_ls"] * 86.4
            q_b = pb["current_yield_ls"] * 86.4
            t_a = pa["transmissivity_m2d"]
            t_b = pb["transmissivity_m2d"]
            s_a = pa["storativity"]
            s_b = pb["storativity"]

            if q_a <= 0 or q_b <= 0:
                continue

            s_self_a = theis_drawdown(q_a, t_a, s_a, well_radius_m, t_days)
            s_self_b = theis_drawdown(q_b, t_b, s_b, well_radius_m, t_days)

            s_b_at_a = theis_drawdown(q_b, t_b, s_b, r, t_days)
            s_a_at_b = theis_drawdown(q_a, t_a, s_a, r, t_days)

            coef_at_a = min(s_b_at_a / s_self_a, 1.0) if s_self_a > 0 else 0.0
            coef_at_b = min(s_a_at_b / s_self_b, 1.0) if s_self_b > 0 else 0.0

            coef_max = max(coef_at_a, coef_at_b)
            if coef_max < min_coefficient:
                continue

            r_mid = r / 2
            dm = theis_drawdown(q_a, t_a, s_a, r_mid, t_days) + theis_drawdown(
                q_b, t_b, s_b, r_mid, t_days
            )

            severity = _severity_from_coef(coef_max)
            dominant = pb["id"] if coef_at_a >= coef_at_b else pa["id"]
            victim = pa["id"] if dominant == pb["id"] else pb["id"]

            pairs.append(
                InterferencePair(
                    well_a=pa["id"],
                    well_b=pb["id"],
                    distance_km=round(r / 1000, 3),
                    coef_at_a=round(coef_at_a, 3),
                    coef_at_b=round(coef_at_b, 3),
                    drawdown_midpoint_m=round(dm, 2),
                    severity=severity,
                    dominant_well=dominant,
                    recommendation=_recommendation(severity, dominant, victim, r / 1000),
                )
            )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    pairs.sort(key=lambda p: (severity_order[p.severity], -max(p.coef_at_a, p.coef_at_b)))

    return InterferenceResult(
        pairs=pairs,
        t_days=t_days,
        wells_analyzed=len(wells_in_bbox),
        pairs_significant=len(pairs),
    )
