"""Context bridge: MapContext from frontend → LLM system prompt section."""
import json
import os
from pathlib import Path

from models.schemas import MapContext

def _get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "./data")


def load_wells_data() -> dict[str, dict]:
    """Load wells from GeoJSON keyed by well ID."""
    path = Path(_get_data_dir()) / "wells.geojson"
    with open(path, encoding="utf-8") as f:
        geojson = json.load(f)

    wells = {}
    for feat in geojson["features"]:
        props = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        data = {**props, "latitude": lat, "longitude": lon}
        wells[props["id"]] = data
    return wells


def _count_visible_wells(wells_data: dict, bbox: list[float]) -> list[str]:
    """Return IDs of wells within bbox."""
    west, south, east, north = bbox
    visible = []
    for wid, data in wells_data.items():
        lon, lat = data["longitude"], data["latitude"]
        if west <= lon <= east and south <= lat <= north:
            visible.append(wid)
    return visible


def build_context_prompt(map_context: MapContext, wells_data: dict) -> str:
    """Build context section for LLM system prompt from current map state."""
    lines = ["## Current Map State"]
    lines.append(f"- Center: ({map_context.center_lat:.4f}, {map_context.center_lng:.4f}), zoom {map_context.zoom}")
    lines.append(f"- Visible area (bbox): {map_context.bbox}")
    lines.append(f"- Active layers: {', '.join(map_context.active_layers)}")

    # Count visible wells
    visible = _count_visible_wells(wells_data, map_context.bbox)
    lines.append(f"- Wells in view: {len(visible)} visible")

    if map_context.filters:
        lines.append(f"- Active filters: {map_context.filters}")

    if "depression_cone" in map_context.active_layers:
        lines.append(
            f"- Depression cone layer: ON, t={map_context.depression_cone_t_days}d, "
            f"mode={map_context.depression_cone_mode}"
        )
    if map_context.interference_visible or "interference" in map_context.active_layers:
        lines.append("- Interference layer: ON (showing significant pairs from analyze_interference)")

    # Selected well details
    if map_context.selected_well_id:
        well = wells_data.get(map_context.selected_well_id)
        if well:
            lines.append(f"\n## Selected Well: {well['name_en']} ({map_context.selected_well_id})")
            lines.append(f"- Cluster: {well['cluster_name']}")
            lines.append(f"- Depth: {well['well_depth_m']}m, Aquifer: {well['aquifer_type']}")
            lines.append(f"- Status: {well['status']}")
            lines.append(f"- Current yield: {well['current_yield_ls']} L/s")
            lines.append(f"- TDS: {well['last_tds_mgl']} mg/L, pH: {well['last_ph']}")
            lines.append(f"- Static water level: {well['static_water_level_m']}m")
            lines.append(f"- Chloride: {well['last_chloride_mgl']} mg/L, Temperature: {well['last_temperature_c']}°C")
            lines.append(f"- Transmissivity: {well['transmissivity_m2d']} m²/day, Storativity: {well['storativity']}")

    return "\n".join(lines)
